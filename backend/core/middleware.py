"""
Morphix â€” Custom Middleware
"""

import logging
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware that logs state-changing API requests (POST, PUT, PATCH, DELETE)
    to the AuditLog model for security and compliance.
    """

    AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    EXCLUDED_PATHS = {"/api/v1/auth/token/refresh/", "/admin/", "/__debug__/"}

    def process_response(self, request, response):
        if request.method not in self.AUDITED_METHODS:
            return response

        if any(request.path.startswith(p) for p in self.EXCLUDED_PATHS):
            return response

        if not hasattr(request, "user") or not request.user.is_authenticated:
            return response

        try:
            from apps.analytics.models import AuditLog

            AuditLog.objects.create(
                user=request.user,
                action=f"{request.method} {request.path}",
                resource_type=self._get_resource_type(request.path),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                details={
                    "status_code": response.status_code,
                    "method": request.method,
                    "path": request.path,
                },
            )
        except Exception:
            # Never let audit logging break the request
            logger.exception("Failed to create audit log")

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    @staticmethod
    def _get_resource_type(path: str) -> str:
        """Extract resource type from URL path."""
        parts = path.strip("/").split("/")
        # /api/v1/files/... â†’ "files"
        if len(parts) >= 3:
            return parts[2]
        return "unknown"


class RequestIDMiddleware(MiddlewareMixin):
    """Adds a unique request ID to each request for tracing."""

    def process_request(self, request):
        request.request_id = str(uuid.uuid4())

    def process_response(self, request, response):
        if hasattr(request, "request_id"):
            response["X-Request-ID"] = request.request_id
        return response
