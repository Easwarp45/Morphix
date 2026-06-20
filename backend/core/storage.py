"""
Morphix â€” Storage Service

Handles S3-compatible file storage operations.
"""

import logging
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage on S3-compatible storage."""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create the S3 bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info("Created S3 bucket: %s", self.bucket_name)
            except ClientError:
                logger.exception("Failed to create S3 bucket: %s", self.bucket_name)

    def generate_s3_key(self, user_id: str, filename: str, folder: str = "uploads") -> str:
        """Generate a unique S3 key for a file."""
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        unique_name = f"{uuid.uuid4().hex}"
        if ext:
            unique_name = f"{unique_name}.{ext}"
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        return f"{folder}/{user_id}/{date_path}/{unique_name}"

    def upload_file(self, file_obj, s3_key: str, content_type: str = None) -> bool:
        """Upload a file object to S3."""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            self.s3_client.upload_fileobj(
                file_obj, self.bucket_name, s3_key, ExtraArgs=extra_args
            )
            logger.info("Uploaded file to S3: %s", s3_key)
            return True
        except ClientError:
            logger.exception("Failed to upload file to S3: %s", s3_key)
            return False

    def upload_bytes(self, data: bytes, s3_key: str, content_type: str = None) -> bool:
        """Upload raw bytes to S3."""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                **extra_args,
            )
            logger.info("Uploaded bytes to S3: %s", s3_key)
            return True
        except ClientError:
            logger.exception("Failed to upload bytes to S3: %s", s3_key)
            return False

    def download_file(self, s3_key: str) -> bytes | None:
        """Download a file from S3 and return its bytes."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=s3_key
            )
            return response["Body"].read()
        except ClientError:
            logger.exception("Failed to download file from S3: %s", s3_key)
            return None

    def generate_presigned_url(self, s3_key: str, expiration: int = None) -> str | None:
        """Generate a pre-signed download URL."""
        if expiration is None:
            expiration = settings.AWS_QUERYSTRING_EXPIRE

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError:
            logger.exception("Failed to generate presigned URL for: %s", s3_key)
            return None

    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name, Key=s3_key
            )
            logger.info("Deleted file from S3: %s", s3_key)
            return True
        except ClientError:
            logger.exception("Failed to delete file from S3: %s", s3_key)
            return False

    def get_file_size(self, s3_key: str) -> int | None:
        """Get file size in bytes."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name, Key=s3_key
            )
            return response["ContentLength"]
        except ClientError:
            return None


# Singleton instance
_storage_service = None


def get_storage_service() -> StorageService:
    """Get or create the storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
