"""
Cloud File Converter — Conversion Model
"""

import uuid

from django.conf import settings
from django.db import models


class Conversion(models.Model):
    """Tracks a file conversion job."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    class ConversionType(models.TextChoices):
        # Documents
        PDF_TO_DOCX = "pdf_to_docx", "PDF → DOCX"
        DOCX_TO_PDF = "docx_to_pdf", "DOCX → PDF"
        TXT_TO_PDF = "txt_to_pdf", "TXT → PDF"
        PDF_TO_TXT = "pdf_to_txt", "PDF → TXT"
        # Images
        PNG_TO_JPG = "png_to_jpg", "PNG → JPG"
        JPG_TO_PNG = "jpg_to_png", "JPG → PNG"
        WEBP_TO_PNG = "webp_to_png", "WEBP → PNG"
        PNG_TO_WEBP = "png_to_webp", "PNG → WEBP"
        # Compression
        IMAGE_COMPRESS = "image_compress", "Image Compression"
        PDF_COMPRESS = "pdf_compress", "PDF Compression"
        # Archive
        ZIP_CREATE = "zip_create", "ZIP Creation"
        ZIP_EXTRACT = "zip_extract", "ZIP Extraction"
        # OCR & AI
        IMAGE_OCR_TO_TXT = "image_ocr_to_txt", "Extract Text (OCR)"
        PDF_OCR_TO_TXT = "pdf_ocr_to_txt", "Extract Scanned Text (OCR)"
        AI_SUMMARIZE = "ai_summarize", "Summarize Document (AI)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversions",
    )
    source_file = models.ForeignKey(
        "files.File",
        on_delete=models.SET_NULL,
        null=True,
        related_name="conversions",
    )
    conversion_type = models.CharField(
        max_length=30,
        choices=ConversionType.choices,
    )
    source_format = models.CharField(max_length=20)
    target_format = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Output
    output_s3_key = models.CharField(max_length=1000, blank=True)
    output_filename = models.CharField(max_length=500, blank=True)
    output_file_size = models.BigIntegerField(default=0)

    # Processing details
    error_message = models.TextField(blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    conversion_options = models.JSONField(default=dict, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True, db_index=True)
    is_batch = models.BooleanField(default=False)
    batch_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_conv_user_created"),
            models.Index(fields=["status"], name="idx_conv_status"),
            models.Index(fields=["celery_task_id"], name="idx_conv_task_id"),
        ]

    def __str__(self):
        return f"{self.source_format} → {self.target_format} ({self.status})"

    @property
    def output_file_size_mb(self):
        return round(self.output_file_size / (1024 * 1024), 2) if self.output_file_size else 0


class DownloadShare(models.Model):
    """Tracks temporary shareable download links for conversions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversion = models.ForeignKey(
        Conversion,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    share_token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "download_shares"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Share {self.share_token[:8]} for {self.conversion}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
