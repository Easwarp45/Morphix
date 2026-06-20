"""
Cloud File Converter — Conversion Serializers
"""

from rest_framework import serializers

from .engine import FORMAT_MAPPING
from .models import Conversion, DownloadShare


class ConversionSerializer(serializers.ModelSerializer):
    """Serializer for conversion details."""

    output_file_size_mb = serializers.FloatField(read_only=True)
    source_file_name = serializers.CharField(
        source="source_file.original_name", read_only=True
    )
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Conversion
        fields = [
            "id",
            "source_file",
            "source_file_name",
            "conversion_type",
            "source_format",
            "target_format",
            "status",
            "is_batch",
            "batch_id",
            "output_filename",
            "output_file_size",
            "output_file_size_mb",
            "processing_time",
            "error_message",
            "download_url",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        if obj.status != Conversion.Status.COMPLETED or not obj.output_s3_key:
            return None
        try:
            from core.storage import get_storage_service

            storage = get_storage_service()
            return storage.generate_presigned_url(obj.output_s3_key)
        except Exception:
            return None


class ConversionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new conversion."""

    source_file_id = serializers.UUIDField()
    conversion_type = serializers.ChoiceField(choices=Conversion.ConversionType.choices)
    options = serializers.DictField(required=False, default=dict)

    def validate_source_file_id(self, value):
        from apps.files.models import File

        user = self.context["request"].user
        try:
            file = File.objects.get(id=value, user=user)
        except File.DoesNotExist:
            raise serializers.ValidationError("File not found.")

        if file.status == File.Status.DELETED:
            raise serializers.ValidationError("File has been deleted.")

        return value

    def validate(self, attrs):
        from apps.files.models import File

        file = File.objects.get(id=attrs["source_file_id"])
        conversion_type = attrs["conversion_type"]

        # Validate that the conversion type is compatible with the file
        available = FORMAT_MAPPING.get(file.file_extension, [])
        valid_types = [fmt["type"] for fmt in available]

        if conversion_type not in valid_types:
            raise serializers.ValidationError(
                {
                    "conversion_type": (
                        f"Conversion type '{conversion_type}' is not available for "
                        f"'{file.file_extension}' files. Available types: {valid_types}"
                    )
                }
            )

        return attrs


class SupportedFormatsSerializer(serializers.Serializer):
    """Serializer for listing supported conversion formats."""

    source_extension = serializers.CharField()
    conversions = serializers.ListField(child=serializers.DictField())


class DownloadShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadShare
        fields = ["id", "share_token", "expires_at", "download_count", "created_at"]
        read_only_fields = fields
