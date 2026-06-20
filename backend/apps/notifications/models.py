"""
Morphix â€” Notification Model
"""

import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """In-app notification for users."""

    class Type(models.TextChoices):
        CONVERSION_COMPLETE = "conversion_complete", "Conversion Complete"
        CONVERSION_FAILED = "conversion_failed", "Conversion Failed"
        STORAGE_WARNING = "storage_warning", "Storage Warning"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"], name="idx_notif_user_read"),
        ]

    def __str__(self):
        return f"{self.title} â†’ {self.user.email}"
