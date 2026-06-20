"""
Morphix â€” Files Celery Tasks
"""

import logging

from celery import shared_task
from django.utils import timezone

from apps.files.models import File
from apps.files.services import FileService
from apps.users.models import User

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_files():
    """Purge expired files from S3 and database, and delete inactive guest users."""
    now = timezone.now()

    # 1. Purge expired uploaded files
    expired_files = File.objects.filter(expires_at__lte=now).exclude(
        status=File.Status.DELETED
    )
    count = 0
    for file_record in expired_files:
        try:
            FileService.delete_file(file_record)
            count += 1
        except Exception as e:
            logger.error("Failed to delete expired file %s: %s", file_record.id, str(e))

    logger.info("Purged %d expired files.", count)

    # 2. Prune inactive guest users who haven't had activity in the last 24 hours
    cutoff = now - timezone.timedelta(hours=24)
    inactive_guests = User.objects.filter(is_guest=True, last_activity__lte=cutoff)
    guest_count = 0
    for guest in inactive_guests:
        # Delete guest's files
        guest_files = File.objects.filter(user=guest).exclude(
            status=File.Status.DELETED
        )
        for f in guest_files:
            try:
                FileService.delete_file(f)
            except Exception:
                pass
        # Delete guest user
        guest.delete()
        guest_count += 1

    logger.info("Pruned %d inactive guest user accounts.", guest_count)
