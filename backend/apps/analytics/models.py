"""
Morphix â€” Analytics Models
"""

import uuid

from django.conf import settings
from django.db import models


class Download(models.Model):
    """Tracks file downloads."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="downloads",
    )
    conversion = models.ForeignKey(
        "converters.Conversion",
        on_delete=models.SET_NULL,
        null=True,
        related_name="downloads",
    )
    file_name = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "downloads"
        ordering = ["-downloaded_at"]
        indexes = [
            models.Index(fields=["user", "-downloaded_at"], name="idx_dl_user_date"),
        ]

    def __str__(self):
        return f"{self.file_name} by {self.user.email}"


class AuditLog(models.Model):
    """Audit trail for security and compliance."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=500, db_index=True)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_audit_user_date"),
            models.Index(fields=["action"], name="idx_audit_action"),
        ]

    def __str__(self):
        return f"{self.action} by {self.user}"
