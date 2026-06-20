"""
Morphix â€” Admin Panel Views
"""

from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.converters.models import Conversion
from apps.files.models import File
from apps.users.models import User
from apps.users.serializers import AdminUserSerializer
from core.permissions import IsAdminUser


class AdminUserListView(generics.ListAPIView):
    """List all users (admin only)."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email", "storage_used"]
    ordering = ["-created_at"]


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """View/update a specific user (admin only)."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()


class AdminDeactivateUserView(APIView):
    """Deactivate a user account (admin only)."""

    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "not_found", "message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.is_active = False
        user.save(update_fields=["is_active"])

        return Response(
            {"success": True, "data": {"message": f"User {user.email} deactivated."}}
        )


class AdminAnalyticsView(APIView):
    """System-wide analytics for admins."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        # User stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_7d = User.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        # Conversion stats
        total_conversions = Conversion.objects.count()
        completed_conversions = Conversion.objects.filter(
            status=Conversion.Status.COMPLETED
        ).count()
        failed_conversions = Conversion.objects.filter(
            status=Conversion.Status.FAILED
        ).count()

        # Storage stats
        total_storage = User.objects.aggregate(total=Sum("storage_used"))["total"] or 0
        total_files = File.objects.exclude(status=File.Status.DELETED).count()

        # Conversions by type
        conversions_by_type = (
            Conversion.objects.values("conversion_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Daily conversions (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily = (
            Conversion.objects.filter(created_at__gte=thirty_days_ago)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # Daily signups (last 30 days)
        daily_signups = (
            User.objects.filter(created_at__gte=thirty_days_ago)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return Response(
            {
                "success": True,
                "data": {
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "new_7d": new_users_7d,
                    },
                    "conversions": {
                        "total": total_conversions,
                        "completed": completed_conversions,
                        "failed": failed_conversions,
                        "success_rate": (
                            round(completed_conversions / total_conversions * 100, 1)
                            if total_conversions > 0
                            else 0
                        ),
                    },
                    "storage": {
                        "total_used": total_storage,
                        "total_used_mb": round(total_storage / (1024 * 1024), 2),
                        "total_files": total_files,
                    },
                    "conversions_by_type": list(conversions_by_type),
                    "daily_conversions": [
                        {"date": str(d["date"]), "count": d["count"]} for d in daily
                    ],
                    "daily_signups": [
                        {"date": str(d["date"]), "count": d["count"]}
                        for d in daily_signups
                    ],
                },
            }
        )


class AdminStorageMonitorView(APIView):
    """Monitor storage usage across all users."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        top_users = (
            User.objects.filter(storage_used__gt=0)
            .order_by("-storage_used")
            .values("id", "email", "storage_used", "storage_limit")[:20]
        )

        total_storage = User.objects.aggregate(total=Sum("storage_used"))["total"] or 0

        return Response(
            {
                "success": True,
                "data": {
                    "total_storage_used": total_storage,
                    "total_storage_used_mb": round(total_storage / (1024 * 1024), 2),
                    "top_users": [
                        {
                            "id": str(u["id"]),
                            "email": u["email"],
                            "storage_used_mb": round(u["storage_used"] / (1024 * 1024), 2),
                            "storage_limit_mb": round(u["storage_limit"] / (1024 * 1024), 2),
                            "usage_percent": round(u["storage_used"] / u["storage_limit"] * 100, 1)
                            if u["storage_limit"] > 0
                            else 0,
                        }
                        for u in top_users
                    ],
                },
            }
        )
