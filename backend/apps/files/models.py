"""
Cloud File Converter — File Model
"""

import uuid

from django.conf import settings
from django.db import models


class File(models.Model):
    """Represents an uploaded file."""

    class Status(models.TextChoices):
        UPLOADING = "uploading", "Uploading"
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        DELETED = "deleted", "Deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="files",
    )
    original_name = models.CharField(max_length=500)
    stored_name = models.CharField(max_length=500)
    s3_key = models.CharField(max_length=1000, db_index=True)
    mime_type = models.CharField(max_length=200)
    file_extension = models.CharField(max_length=20)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
        db_index=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(db_index=True, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "files"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_files_user_created"),
            models.Index(fields=["status"], name="idx_files_status"),
        ]

    def __str__(self):
        return f"{self.original_name} ({self.file_extension})"

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def is_image(self):
        return self.mime_type.startswith("image/")

    @property
    def is_document(self):
        return self.file_extension in {".pdf", ".docx", ".doc", ".txt"}
