"""
Cloud File Converter — Analytics Views
"""

from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.converters.models import Conversion
from apps.files.models import File

from .models import Download


class DashboardStatsView(APIView):
    """Get dashboard statistics for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Total files
        total_files = File.objects.filter(user=user).exclude(
            status=File.Status.DELETED
        ).count()

        # Total conversions
        total_conversions = Conversion.objects.filter(user=user).count()
        completed_conversions = Conversion.objects.filter(
            user=user, status=Conversion.Status.COMPLETED
        ).count()
        failed_conversions = Conversion.objects.filter(
            user=user, status=Conversion.Status.FAILED
        ).count()

        # Total downloads
        total_downloads = Download.objects.filter(user=user).count()

        # Storage info
        storage_used = user.storage_used
        storage_limit = user.storage_limit
        storage_percent = user.storage_usage_percent

        # Conversions by type
        conversions_by_type = (
            Conversion.objects.filter(user=user, status=Conversion.Status.COMPLETED)
            .values("conversion_type")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        # Recent activity (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_conversions = (
            Conversion.objects.filter(user=user, created_at__gte=seven_days_ago)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return Response(
            {
                "success": True,
                "data": {
                    "total_files": total_files,
                    "total_conversions": total_conversions,
                    "completed_conversions": completed_conversions,
                    "failed_conversions": failed_conversions,
                    "total_downloads": total_downloads,
                    "storage": {
                        "used": storage_used,
                        "limit": storage_limit,
                        "percent": storage_percent,
                        "used_mb": round(storage_used / (1024 * 1024), 2),
                        "limit_mb": round(storage_limit / (1024 * 1024), 2),
                    },
                    "conversions_by_type": list(conversions_by_type),
                    "daily_conversions": [
                        {"date": str(d["date"]), "count": d["count"]}
                        for d in daily_conversions
                    ],
                },
            }
        )


class ConversionHistoryView(APIView):
    """Get conversion history for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversions = (
            Conversion.objects.filter(user=request.user)
            .select_related("source_file")
            .order_by("-created_at")[:50]
        )

        history = []
        for conv in conversions:
            history.append(
                {
                    "id": str(conv.id),
                    "source_file_name": conv.source_file.original_name if conv.source_file else "Deleted",
                    "conversion_type": conv.conversion_type,
                    "source_format": conv.source_format,
                    "target_format": conv.target_format,
                    "status": conv.status,
                    "output_filename": conv.output_filename,
                    "processing_time": conv.processing_time,
                    "created_at": conv.created_at.isoformat(),
                }
            )

        return Response({"success": True, "data": history})


class UsageStatsView(APIView):
    """Get storage usage breakdown."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Files by type
        files_by_type = (
            File.objects.filter(user=user)
            .exclude(status=File.Status.DELETED)
            .values("file_extension")
            .annotate(count=Count("id"), total_size=Sum("file_size"))
            .order_by("-total_size")
        )

        return Response(
            {
                "success": True,
                "data": {
                    "storage_used": user.storage_used,
                    "storage_limit": user.storage_limit,
                    "storage_percent": user.storage_usage_percent,
                    "files_by_type": [
                        {
                            "extension": f["file_extension"],
                            "count": f["count"],
                            "total_size": f["total_size"],
                            "total_size_mb": round(f["total_size"] / (1024 * 1024), 2),
                        }
                        for f in files_by_type
                    ],
                },
            }
        )
