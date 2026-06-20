"""
Cloud File Converter — Conversion Views
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import Download
from apps.files.models import File
from core.permissions import IsOwner
from core.storage import get_storage_service
from core.throttling import ConversionRateThrottle

from .engine import FORMAT_MAPPING
from .models import Conversion, DownloadShare
from .serializers import ConversionCreateSerializer, ConversionSerializer, DownloadShareSerializer
from .tasks import process_conversion, zip_batch_conversions


class ConversionCreateView(APIView):
    """Start a new file conversion."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ConversionRateThrottle]

    def post(self, request):
        serializer = ConversionCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        source_file = File.objects.get(id=serializer.validated_data["source_file_id"])
        conversion_type = serializer.validated_data["conversion_type"]
        options = serializer.validated_data.get("options", {})

        # Determine source and target formats
        source_format = source_file.file_extension
        format_info = next(
            (f for f in FORMAT_MAPPING.get(source_format, []) if f["type"] == conversion_type),
            None,
        )
        target_format = format_info["target"] if format_info else ""

        # Create conversion record
        conversion = Conversion.objects.create(
            user=request.user,
            source_file=source_file,
            conversion_type=conversion_type,
            source_format=source_format,
            target_format=target_format,
            conversion_options=options,
            status=Conversion.Status.PENDING,
        )

        # Update source file status
        source_file.status = File.Status.PROCESSING
        source_file.save(update_fields=["status", "updated_at"])

        # Queue the conversion task
        task = process_conversion.delay(str(conversion.id))
        conversion.celery_task_id = task.id
        conversion.save(update_fields=["celery_task_id"])

        return Response(
            {
                "success": True,
                "data": ConversionSerializer(conversion).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ConversionListView(generics.ListAPIView):
    """List all conversions for the authenticated user."""

    serializer_class = ConversionSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Conversion.objects.filter(user=self.request.user).select_related(
            "source_file"
        )


class ConversionDetailView(generics.RetrieveAPIView):
    """Get conversion status and details."""

    serializer_class = ConversionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Conversion.objects.filter(user=self.request.user).select_related(
            "source_file"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})


class ConversionDownloadView(APIView):
    """Download a converted file."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            conversion = Conversion.objects.get(id=pk, user=request.user)
        except Conversion.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "not_found", "message": "Conversion not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if conversion.status != Conversion.Status.COMPLETED:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "not_ready",
                        "message": f"Conversion is {conversion.status}, not yet completed.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        storage = get_storage_service()
        download_url = storage.generate_presigned_url(conversion.output_s3_key)

        if not download_url:
            return Response(
                {"success": False, "error": {"code": "download_error", "message": "Failed to generate download URL."}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Track download
        Download.objects.create(
            user=request.user,
            conversion=conversion,
            file_name=conversion.output_filename,
            file_size=conversion.output_file_size,
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )

        return Response(
            {
                "success": True,
                "data": {
                    "download_url": download_url,
                    "filename": conversion.output_filename,
                    "file_size": conversion.output_file_size,
                },
            }
        )


class SupportedFormatsView(APIView):
    """List all supported conversion formats."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        formats = []
        for ext, conversions in FORMAT_MAPPING.items():
            formats.append(
                {
                    "source_extension": ext,
                    "conversions": conversions,
                }
            )

        return Response({"success": True, "data": formats})


class BatchConversionCreateView(APIView):
    """Start batch file conversions under a single batch_id."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ConversionRateThrottle]

    def post(self, request):
        import uuid

        conversions_data = request.data.get("conversions", [])
        if not conversions_data:
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": "No conversions data provided."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch_id = uuid.uuid4()
        created_conversions = []
        errors = []

        for item in conversions_data:
            serializer = ConversionCreateSerializer(
                data=item, context={"request": request}
            )
            if not serializer.is_valid():
                errors.append({"item": item, "errors": serializer.errors})
                continue

            source_file = File.objects.get(id=serializer.validated_data["source_file_id"])
            conversion_type = serializer.validated_data["conversion_type"]
            options = serializer.validated_data.get("options", {})

            source_format = source_file.file_extension
            format_info = next(
                (f for f in FORMAT_MAPPING.get(source_format, []) if f["type"] == conversion_type),
                None,
            )
            target_format = format_info["target"] if format_info else ""

            conversion = Conversion.objects.create(
                user=request.user,
                source_file=source_file,
                conversion_type=conversion_type,
                source_format=source_format,
                target_format=target_format,
                conversion_options=options,
                status=Conversion.Status.PENDING,
                is_batch=True,
                batch_id=batch_id,
            )

            source_file.status = File.Status.PROCESSING
            source_file.save(update_fields=["status", "updated_at"])

            task = process_conversion.delay(str(conversion.id))
            conversion.celery_task_id = task.id
            conversion.save(update_fields=["celery_task_id"])

            created_conversions.append(ConversionSerializer(conversion).data)

        return Response(
            {
                "success": True,
                "data": {
                    "batch_id": str(batch_id),
                    "conversions": created_conversions,
                    "errors": errors,
                },
            },
            status=status.HTTP_201_CREATED if created_conversions else status.HTTP_400_BAD_REQUEST,
        )


class BatchConversionStatusView(APIView):
    """Retrieve status of all conversions in a batch."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, batch_id):
        conversions = Conversion.objects.filter(batch_id=batch_id, user=request.user)
        if not conversions.exists():
            return Response(
                {"success": False, "error": {"code": "not_found", "message": "Batch not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConversionSerializer(conversions, many=True)
        return Response(
            {
                "success": True,
                "data": {
                    "batch_id": batch_id,
                    "conversions": serializer.data,
                    "all_completed": all(c.status == Conversion.Status.COMPLETED for c in conversions),
                    "any_failed": any(c.status == Conversion.Status.FAILED for c in conversions),
                },
            }
        )


class BatchZipCreateView(APIView):
    """Zip all completed files in a batch into a single download."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, batch_id):
        # Validate that the batch belongs to the user
        conversions = Conversion.objects.filter(
            batch_id=batch_id, user=request.user, status=Conversion.Status.COMPLETED
        )
        if not conversions.exists():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "not_found",
                        "message": "No completed conversions found for this batch.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a placeholder conversion for the ZIP file
        zip_conversion = Conversion.objects.create(
            user=request.user,
            conversion_type=Conversion.ConversionType.ZIP_CREATE,
            source_format="batch",
            target_format=".zip",
            output_filename=f"batch_archive_{str(batch_id)[:8]}.zip",
            status=Conversion.Status.PENDING,
            is_batch=True,
            batch_id=batch_id,
        )

        # Queue zip task
        zip_batch_conversions.delay(str(batch_id), str(zip_conversion.id))

        return Response(
            {"success": True, "data": ConversionSerializer(zip_conversion).data},
            status=status.HTTP_202_ACCEPTED,
        )


class CreateDownloadShareView(APIView):
    """Generate a shareable download link for a completed conversion."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            conversion = Conversion.objects.get(id=pk, user=request.user)
        except Conversion.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "not_found", "message": "Conversion not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if conversion.status != Conversion.Status.COMPLETED:
            return Response(
                {"success": False, "error": {"code": "not_ready", "message": "Conversion is not completed."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from datetime import timedelta
        from django.utils import timezone
        from django.utils.crypto import get_random_string

        # Generate token
        token = get_random_string(32)
        expires_at = timezone.now() + timedelta(hours=24)  # share link valid for 24h

        share = DownloadShare.objects.create(
            conversion=conversion, share_token=token, expires_at=expires_at
        )

        share_url = f"/share/{token}"

        return Response(
            {
                "success": True,
                "data": {
                    "share_token": token,
                    "share_url": share_url,
                    "expires_at": expires_at,
                },
            }
        )


class PublicDownloadShareView(APIView):
    """Public unauthenticated access to download shared files."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            share = DownloadShare.objects.select_related("conversion", "conversion__user").get(
                share_token=token
            )
        except DownloadShare.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "not_found", "message": "Share link invalid or expired."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if share.is_expired:
            return Response(
                {"success": False, "error": {"code": "expired", "message": "This share link has expired."}},
                status=status.HTTP_410_GONE,
            )

        storage = get_storage_service()
        download_url = storage.generate_presigned_url(share.conversion.output_s3_key)

        if not download_url:
            return Response(
                {
                    "success": False,
                    "error": {"code": "download_error", "message": "Failed to generate download link."},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Track usage
        share.download_count += 1
        share.save(update_fields=["download_count"])

        # Track overall download log
        Download.objects.create(
            user=share.conversion.user,
            conversion=share.conversion,
            file_name=share.conversion.output_filename,
            file_size=share.conversion.output_file_size,
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )

        return Response(
            {
                "success": True,
                "data": {
                    "download_url": download_url,
                    "filename": share.conversion.output_filename,
                    "file_size": share.conversion.output_file_size,
                },
            }
        )
