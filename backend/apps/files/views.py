"""
Cloud File Converter — File Views
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, parsers, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwner
from core.throttling import UploadRateThrottle

from .models import File
from .serializers import FileSerializer, FileUploadSerializer
from .services import FileService


class FileUploadView(APIView):
    """Upload one or more files."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    throttle_classes = [UploadRateThrottle]

    def post(self, request):
        files = request.FILES.getlist("files")
        if not files:
            # Try single file upload
            single = request.FILES.get("file")
            if single:
                files = [single]

        if not files:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "no_files",
                        "message": "No files were provided.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.conf import settings

        if len(files) > settings.MAX_FILES_PER_UPLOAD:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "too_many_files",
                        "message": f"Maximum {settings.MAX_FILES_PER_UPLOAD} files per upload.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_files = []
        errors = []

        for f in files:
            try:
                file_record = FileService.upload_file(request.user, f)
                uploaded_files.append(FileSerializer(file_record).data)
            except Exception as e:
                errors.append({"file": f.name, "error": str(e)})

        return Response(
            {
                "success": True,
                "data": {
                    "uploaded": uploaded_files,
                    "errors": errors,
                    "total_uploaded": len(uploaded_files),
                    "total_errors": len(errors),
                },
            },
            status=status.HTTP_201_CREATED if uploaded_files else status.HTTP_400_BAD_REQUEST,
        )


class FileListView(generics.ListAPIView):
    """List all files for the authenticated user."""

    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["original_name"]
    ordering_fields = ["created_at", "file_size", "original_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return File.objects.filter(user=self.request.user).exclude(
            status=File.Status.DELETED
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # The paginator already wraps the response if pagination is enabled
        return response


class FileDetailView(generics.RetrieveDestroyAPIView):
    """Get file details or delete a file."""

    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return File.objects.filter(user=self.request.user).exclude(
            status=File.Status.DELETED
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        FileService.delete_file(instance)
        return Response(
            {
                "success": True,
                "data": {"message": f"File '{instance.original_name}' deleted."},
            },
            status=status.HTTP_200_OK,
        )
