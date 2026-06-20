"""
Morphix â€” Celery Tasks for File Conversion
"""

import logging
import time

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_conversion_update(conversion):
    """Send real-time update of conversion status via Channel Layer."""
    from apps.converters.serializers import ConversionSerializer

    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            data = ConversionSerializer(conversion).data
            async_to_sync(channel_layer.group_send)(
                f"user_{conversion.user_id}",
                {
                    "type": "conversion_update",
                    "data": {
                        "event": "conversion_status",
                        "conversion": data,
                    },
                },
            )
    except Exception as e:
        logger.warning("Failed to send real-time WebSocket update: %s", str(e))


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=240,
    time_limit=300,
    acks_late=True,
)
def process_conversion(self, conversion_id: str):
    """
    Process a file conversion asynchronously.

    This task:
    1. Downloads the source file from S3
    2. Runs the appropriate converter
    3. Uploads the result to S3
    4. Updates the conversion record
    """
    from apps.converters.engine import get_converter
    from apps.converters.models import Conversion
    from apps.files.models import File
    from core.storage import get_storage_service

    try:
        conversion = Conversion.objects.select_related("source_file", "user").get(
            id=conversion_id
        )
    except Conversion.DoesNotExist:
        logger.error("Conversion not found: %s", conversion_id)
        return

    # Update status to processing
    conversion.status = Conversion.Status.PROCESSING
    conversion.started_at = timezone.now()
    conversion.celery_task_id = self.request.id
    conversion.save(update_fields=["status", "started_at", "celery_task_id"])
    send_conversion_update(conversion)

    start_time = time.time()

    try:
        storage = get_storage_service()

        # 1. Download source file from S3
        source_bytes = storage.download_file(conversion.source_file.s3_key)
        if source_bytes is None:
            raise Exception("Failed to download source file from storage.")

        # 2. Get the appropriate converter and run conversion
        converter = get_converter(conversion.conversion_type)
        output_bytes, output_ext = converter.convert(
            source_bytes, conversion.conversion_options
        )

        # 3. Generate output filename
        source_name = conversion.source_file.original_name
        base_name = source_name.rsplit(".", 1)[0] if "." in source_name else source_name
        output_filename = f"{base_name}_converted{output_ext}"

        # 4. Upload result to S3
        output_s3_key = storage.generate_s3_key(
            str(conversion.user_id), output_filename, folder="conversions"
        )

        # Determine content type for the output
        content_type_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".zip": "application/zip",
        }
        output_content_type = content_type_map.get(output_ext, "application/octet-stream")

        success = storage.upload_bytes(output_bytes, output_s3_key, output_content_type)
        if not success:
            raise Exception("Failed to upload converted file to storage.")

        # 5. Update conversion record
        processing_time = time.time() - start_time
        conversion.status = Conversion.Status.COMPLETED
        conversion.output_s3_key = output_s3_key
        conversion.output_filename = output_filename
        conversion.output_file_size = len(output_bytes)
        conversion.processing_time = round(processing_time, 3)
        conversion.completed_at = timezone.now()
        conversion.save()

        # Update source file status
        conversion.source_file.status = File.Status.COMPLETED
        conversion.source_file.save(update_fields=["status", "updated_at"])

        # Update user storage (add converted file size)
        conversion.user.add_storage_usage(len(output_bytes))

        # Send WebSocket update
        send_conversion_update(conversion)

        logger.info(
            "Conversion completed: %s (%s â†’ %s) in %.2fs",
            conversion_id,
            conversion.source_format,
            conversion.target_format,
            processing_time,
        )

    except Exception as exc:
        processing_time = time.time() - start_time
        conversion.status = Conversion.Status.FAILED
        conversion.error_message = str(exc)[:1000]
        conversion.processing_time = round(processing_time, 3)
        conversion.completed_at = timezone.now()
        conversion.save()
        send_conversion_update(conversion)

        logger.exception("Conversion failed: %s â€” %s", conversion_id, str(exc))

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)


@shared_task
def zip_batch_conversions(batch_id: str, zip_conversion_id: str):
    """
    Collect all completed files from a batch, zip them together,
    and save the ZIP as the output of the specified zip_conversion_id.
    """
    import io
    import zipfile
    from apps.converters.models import Conversion
    from core.storage import get_storage_service

    try:
        zip_conversion = Conversion.objects.get(id=zip_conversion_id)
    except Conversion.DoesNotExist:
        logger.error("ZIP Conversion not found: %s", zip_conversion_id)
        return

    zip_conversion.status = Conversion.Status.PROCESSING
    zip_conversion.started_at = timezone.now()
    zip_conversion.save(update_fields=["status", "started_at"])
    send_conversion_update(zip_conversion)

    try:
        storage = get_storage_service()
        # Find all completed conversions in this batch
        conversions = Conversion.objects.filter(
            batch_id=batch_id,
            status=Conversion.Status.COMPLETED
        ).exclude(id=zip_conversion_id)

        if not conversions.exists():
            raise Exception("No completed conversions found in this batch.")

        # Create ZIP in-memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for conv in conversions:
                file_bytes = storage.download_file(conv.output_s3_key)
                if file_bytes:
                    zf.writestr(conv.output_filename, file_bytes)

        zip_data = zip_buffer.getvalue()

        # Upload ZIP to S3
        output_s3_key = storage.generate_s3_key(
            str(zip_conversion.user_id),
            zip_conversion.output_filename,
            folder="conversions"
        )
        success = storage.upload_bytes(zip_data, output_s3_key, "application/zip")
        if not success:
            raise Exception("Failed to upload ZIP archive to storage.")

        zip_conversion.status = Conversion.Status.COMPLETED
        zip_conversion.output_s3_key = output_s3_key
        zip_conversion.output_file_size = len(zip_data)
        zip_conversion.completed_at = timezone.now()
        zip_conversion.save()
        send_conversion_update(zip_conversion)

        # Update user storage
        zip_conversion.user.add_storage_usage(len(zip_data))

    except Exception as exc:
        zip_conversion.status = Conversion.Status.FAILED
        zip_conversion.error_message = str(exc)
        zip_conversion.completed_at = timezone.now()
        zip_conversion.save()
        send_conversion_update(zip_conversion)
        logger.exception("Failed to zip batch conversions: %s", batch_id)
