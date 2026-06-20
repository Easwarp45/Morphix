"""
Cloud File Converter — File Service Layer
"""

import logging
import os

from django.conf import settings

from core.exceptions import FileTooLargeError, StorageLimitExceededError, UnsupportedFormatError
from core.storage import get_storage_service

from .models import File

logger = logging.getLogger(__name__)


class FileService:
    """Service for file upload and management operations."""

    @staticmethod
    def upload_file(user, uploaded_file) -> File:
        """
        Upload a file for a user.

        - Validates file size and type
        - Uploads to S3
        - Creates File record
        - Updates user storage usage
        """
        # Determine limits based on guest status
        if user.is_guest:
            max_size = settings.GUEST_MAX_UPLOAD_SIZE
            max_size_mb = settings.GUEST_MAX_UPLOAD_SIZE_MB
            concurrent_limit = settings.GUEST_CONCURRENT_LIMIT
        else:
            max_size = settings.USER_MAX_UPLOAD_SIZE
            max_size_mb = settings.USER_MAX_UPLOAD_SIZE_MB
            concurrent_limit = settings.USER_CONCURRENT_LIMIT

        # Validate file size
        if uploaded_file.size > max_size:
            raise FileTooLargeError(
                f"File size ({uploaded_file.size / (1024*1024):.1f}MB) exceeds "
                f"maximum allowed ({max_size_mb}MB)."
            )

        # Validate extension
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise UnsupportedFormatError(
                f"File type '{ext}' is not supported."
            )

        # Check concurrency quota
        active_count = File.objects.filter(
            user=user,
            status__in=[File.Status.UPLOADING, File.Status.PROCESSING]
        ).count()
        if active_count >= concurrent_limit:
            raise Exception(
                f"Concurrency limit reached ({concurrent_limit}). "
                "Please wait for your active conversions to complete."
            )

        # Check storage limit
        if user.storage_used + uploaded_file.size > user.storage_limit:
            raise StorageLimitExceededError(
                "You have exceeded your storage limit. "
                "Please delete some files or upgrade your plan."
            )

        # Upload to S3
        storage = get_storage_service()
        s3_key = storage.generate_s3_key(
            str(user.id), uploaded_file.name, folder="uploads"
        )

        success = storage.upload_file(
            uploaded_file, s3_key, content_type=uploaded_file.content_type
        )
        if not success:
            raise Exception("Failed to upload file to storage.")

        # Create file record
        from django.utils import timezone
        if user.is_guest:
            expires_at = timezone.now() + timezone.timedelta(hours=1)
        else:
            expires_at = timezone.now() + timezone.timedelta(hours=24)

        file_record = File.objects.create(
            user=user,
            original_name=uploaded_file.name,
            stored_name=os.path.basename(s3_key),
            s3_key=s3_key,
            mime_type=uploaded_file.content_type,
            file_extension=ext,
            file_size=uploaded_file.size,
            status=File.Status.UPLOADED,
            expires_at=expires_at,
            metadata={
                "original_content_type": uploaded_file.content_type,
            },
        )

        # Update user storage and last activity
        user.last_activity = timezone.now()
        user.add_storage_usage(uploaded_file.size)

        logger.info(
            "File uploaded: %s (%s bytes) by user %s",
            file_record.original_name,
            file_record.file_size,
            user.email,
        )

        return file_record

    @staticmethod
    def delete_file(file_record: File) -> bool:
        """Delete a file from S3 and mark as deleted."""
        storage = get_storage_service()

        # Delete from S3
        storage.delete_file(file_record.s3_key)

        # Update user storage
        file_record.user.reduce_storage_usage(file_record.file_size)

        # Mark as deleted
        file_record.status = File.Status.DELETED
        file_record.save(update_fields=["status", "updated_at"])

        logger.info(
            "File deleted: %s by user %s",
            file_record.original_name,
            file_record.user.email,
        )

        return True

    @staticmethod
    def get_user_files(user, status_filter=None, search_query=None):
        """Get files for a user with optional filtering."""
        queryset = File.objects.filter(user=user).exclude(
            status=File.Status.DELETED
        )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if search_query:
            queryset = queryset.filter(original_name__icontains=search_query)

        return queryset
