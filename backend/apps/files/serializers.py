"""
Cloud File Converter — File Serializers
"""

from rest_framework import serializers

from .models import File


class FileSerializer(serializers.ModelSerializer):
    """Serializer for file listing and details."""

    file_size_mb = serializers.FloatField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    is_document = serializers.BooleanField(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "original_name",
            "mime_type",
            "file_extension",
            "file_size",
            "file_size_mb",
            "status",
            "is_image",
            "is_document",
            "metadata",
            "download_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        """Generate pre-signed download URL."""
        if obj.status == File.Status.DELETED:
            return None
        try:
            from core.storage import get_storage_service

            storage = get_storage_service()
            return storage.generate_presigned_url(obj.s3_key)
        except Exception:
            return None


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload validation."""

    file = serializers.FileField()

    def validate_file(self, value):
        from django.conf import settings
        import os

        # Check file size
        if value.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f"File size ({value.size / (1024*1024):.1f}MB) exceeds "
                f"maximum allowed ({settings.MAX_UPLOAD_SIZE_MB}MB)."
            )

        # Check extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise serializers.ValidationError(
                f"File type '{ext}' is not supported. "
                f"Supported types: {', '.join(sorted(settings.ALLOWED_UPLOAD_EXTENSIONS))}"
            )

        # Check MIME type
        if value.content_type not in settings.ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"MIME type '{value.content_type}' is not supported."
            )

        return value
