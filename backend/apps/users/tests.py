"""
Morphix â€” User Tests
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.users.models import User


# =============================================================================
# Model Tests
# =============================================================================


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email="newuser@example.com",
            password="securepass123",
            first_name="New",
            last_name="User",
        )
        assert user.email == "newuser@example.com"
        assert user.check_password("securepass123")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.full_name == "New User"

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="super@example.com",
            password="superpass123",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_email_normalized(self):
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM", password="pass123"
        )
        assert user.email == "Test@example.com"

    def test_storage_tracking(self):
        user = User.objects.create_user(email="s@e.com", password="p")
        assert user.storage_used == 0
        user.add_storage_usage(1024)
        assert user.storage_used == 1024
        user.reduce_storage_usage(512)
        assert user.storage_used == 512
        user.reduce_storage_usage(9999)
        assert user.storage_used == 0  # Cannot go negative


# =============================================================================
# API Tests
# =============================================================================


@pytest.mark.django_db
class TestAuthAPI:
    def test_register(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "new@example.com",
                "password1": "securepass123!",
                "password2": "securepass123!",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)

    def test_login(self, api_client, user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "testpass123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_login_wrong_password(self, api_client, user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_get_profile(self, auth_client, user):
        response = auth_client.get("/api/v1/auth/user/")
        assert response.status_code == status.HTTP_200_OK

    def test_update_profile(self, auth_client, user):
        response = auth_client.patch(
            "/api/v1/auth/user/",
            {"first_name": "Updated"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_profile(self, api_client):
        response = api_client.get("/api/v1/auth/user/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password(self, auth_client, user):
        response = auth_client.post(
            "/api/v1/auth/password/change/",
            {"old_password": "testpass123", "new_password": "newpass12345"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_current(self, auth_client, user):
        response = auth_client.post(
            "/api/v1/auth/password/change/",
            {"old_password": "wrong", "new_password": "newpass12345"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
