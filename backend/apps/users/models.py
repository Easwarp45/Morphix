"""
Cloud File Converter — Custom User Model
"""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email as the unique identifier."""

    class AuthProvider(models.TextChoices):
        EMAIL = "email", "Email"
        GOOGLE = "google", "Google"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    auth_provider = models.CharField(
        max_length=20,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL,
    )
    is_guest = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Storage tracking
    storage_used = models.BigIntegerField(default=0, help_text="Storage used in bytes")
    storage_limit = models.BigIntegerField(
        default=settings.DEFAULT_STORAGE_LIMIT,
        help_text="Storage limit in bytes",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        if self.is_guest:
            return "Guest User"
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def storage_remaining(self):
        return max(0, self.storage_limit - self.storage_used)

    @property
    def storage_usage_percent(self):
        if self.storage_limit == 0:
            return 100.0
        return round((self.storage_used / self.storage_limit) * 100, 2)

    def add_storage_usage(self, size_bytes: int):
        """Increase storage usage."""
        self.storage_used += size_bytes
        self.save(update_fields=["storage_used", "updated_at"])

    def reduce_storage_usage(self, size_bytes: int):
        """Decrease storage usage."""
        self.storage_used = max(0, self.storage_used - size_bytes)
        self.save(update_fields=["storage_used", "updated_at"])
