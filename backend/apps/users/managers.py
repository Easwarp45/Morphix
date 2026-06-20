"""
Cloud File Converter — User Manager
"""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Custom manager for User model with email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def create_guest(self):
        """Create and return a guest user."""
        import uuid
        from django.conf import settings
        guest_email = f"guest_{uuid.uuid4().hex}@cloudconv.local"
        user = self.model(
            email=guest_email,
            is_guest=True,
            storage_limit=settings.GUEST_STORAGE_LIMIT
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user
