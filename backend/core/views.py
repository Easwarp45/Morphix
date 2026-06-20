"""
Cloud File Converter — Core Shared Views
"""

import logging
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.storage import get_storage_service

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Endpoint for load balancers and system monitoring tools.
    Verifies connection status for Database, Cache (Redis), and Storage (S3).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        health_status = {
            "status": "healthy",
            "database": "up",
            "redis": "up",
            "storage": "up",
            "timestamp": timezone.now().isoformat(),
        }

        # 1. Verify Database Health
        try:
            connection.ensure_connection()
        except Exception as e:
            logger.error("Healthcheck: Database connection failed. Error: %s", str(e))
            health_status["database"] = "down"
            health_status["status"] = "unhealthy"

        # 2. Verify Redis Cache Health
        try:
            cache.set("health_check_ping", "ok", timeout=5)
            val = cache.get("health_check_ping")
            if val != "ok":
                health_status["redis"] = "down"
                health_status["status"] = "unhealthy"
        except Exception as e:
            logger.error("Healthcheck: Redis cache ping failed. Error: %s", str(e))
            health_status["redis"] = "down"
            health_status["status"] = "unhealthy"

        # 3. Verify S3-Compatible Storage Health
        try:
            storage = get_storage_service()
            storage.client.list_buckets()
        except Exception as e:
            logger.error("Healthcheck: Storage client bucket list query failed. Error: %s", str(e))
            health_status["storage"] = "down"
            health_status["status"] = "unhealthy"

        # 4. Respond based on aggregated health status
        if health_status["status"] == "healthy":
            return Response(health_status, status=status.HTTP_200_OK)
        else:
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
