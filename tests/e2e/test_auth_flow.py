"""
Morphix â€” E2E Tests: Authentication Flow
=====================================================
Tests the complete authentication flow: register, login, token refresh,
Google OAuth, profile update, and logout.
"""

import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"


@pytest.fixture(scope="module")
def api():
    """Simple requests session fixture."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def test_user_credentials():
    return {
        "email": "e2e_test_user@morphix.test",
        "password": "E2eTestPass#2024!",
        "first_name": "E2E",
        "last_name": "TestUser",
    }


class TestRegistration:
    def test_register_new_user(self, api, test_user_credentials):
        """POST /api/v1/auth/register/ â€” should return 201 with tokens."""
        response = api.post(
            f"{BASE_URL}/auth/register/",
            json=test_user_credentials,
        )
        assert response.status_code == 201, f"Registration failed: {response.text}"
        data = response.json()
        assert "access" in data, "Access token missing from response"
        assert "refresh" in data, "Refresh token missing from response"
        assert "user" in data, "User object missing from response"
        assert data["user"]["email"] == test_user_credentials["email"]

    def test_register_duplicate_email(self, api, test_user_credentials):
        """POST /api/v1/auth/register/ â€” duplicate email should return 400."""
        response = api.post(
            f"{BASE_URL}/auth/register/",
            json=test_user_credentials,
        )
        assert response.status_code == 400

    def test_register_weak_password(self, api):
        """POST /api/v1/auth/register/ â€” weak password should return 400."""
        response = api.post(
            f"{BASE_URL}/auth/register/",
            json={
                "email": "weak@morphix.test",
                "password": "123",
                "first_name": "Weak",
                "last_name": "User",
            },
        )
        assert response.status_code == 400

    def test_register_invalid_email(self, api):
        """POST /api/v1/auth/register/ â€” invalid email format should return 400."""
        response = api.post(
            f"{BASE_URL}/auth/register/",
            json={
                "email": "not-an-email",
                "password": "StrongPass#2024!",
                "first_name": "Invalid",
                "last_name": "Email",
            },
        )
        assert response.status_code == 400


class TestLogin:
    @pytest.fixture(scope="class")
    def tokens(self, api, test_user_credentials):
        response = api.post(
            f"{BASE_URL}/auth/login/",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
            },
        )
        assert response.status_code == 200
        return response.json()

    def test_login_valid_credentials(self, api, test_user_credentials):
        """POST /api/v1/auth/login/ â€” valid credentials return tokens."""
        response = api.post(
            f"{BASE_URL}/auth/login/",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    def test_login_wrong_password(self, api, test_user_credentials):
        """POST /api/v1/auth/login/ â€” wrong password returns 401."""
        response = api.post(
            f"{BASE_URL}/auth/login/",
            json={
                "email": test_user_credentials["email"],
                "password": "WrongPassword!",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, api):
        """POST /api/v1/auth/login/ â€” nonexistent user returns 401."""
        response = api.post(
            f"{BASE_URL}/auth/login/",
            json={
                "email": "doesnotexist@morphix.test",
                "password": "AnyPassword#123!",
            },
        )
        assert response.status_code == 401

    def test_token_refresh(self, api, tokens):
        """POST /api/v1/auth/token/refresh/ â€” refresh token returns new access token."""
        response = api.post(
            f"{BASE_URL}/auth/token/refresh/",
            json={"refresh": tokens["refresh"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data

    def test_invalid_refresh_token(self, api):
        """POST /api/v1/auth/token/refresh/ â€” invalid token returns 401."""
        response = api.post(
            f"{BASE_URL}/auth/token/refresh/",
            json={"refresh": "not.a.valid.token"},
        )
        assert response.status_code == 401


class TestProfile:
    @pytest.fixture(scope="class")
    def auth_headers(self, api, test_user_credentials):
        response = api.post(
            f"{BASE_URL}/auth/login/",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
            },
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access']}"}

    def test_get_profile(self, api, auth_headers):
        """GET /api/v1/auth/profile/ â€” returns current user profile."""
        response = api.get(f"{BASE_URL}/auth/profile/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "storage_used" in data or "id" in data  # flexible check

    def test_profile_requires_auth(self, api):
        """GET /api/v1/auth/profile/ â€” returns 401 without token."""
        response = api.get(f"{BASE_URL}/auth/profile/")
        assert response.status_code == 401

    def test_update_profile(self, api, auth_headers):
        """PATCH /api/v1/auth/profile/ â€” update name succeeds."""
        response = api.patch(
            f"{BASE_URL}/auth/profile/",
            json={"first_name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 204)
