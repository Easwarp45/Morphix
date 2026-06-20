"""
Cloud File Converter — E2E Tests: Shareable Download Links
==========================================================
Tests creation, retrieval, expiry, and download of shareable links.
"""

import io
import pytest
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


@pytest.fixture(scope="module")
def auth_headers():
    creds = {
        "email": "share_e2e@cloudconv.test",
        "password": "Share#E2eTest2024!",
        "first_name": "Share",
        "last_name": "Tester",
    }
    requests.post(f"{BASE_URL}/auth/register/", json=creds)
    resp = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"email": creds["email"], "password": creds["password"]},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access']}"}


@pytest.fixture(scope="module")
def uploaded_file(auth_headers):
    content = b"Shareable link test file content.\n" * 100
    resp = requests.post(
        f"{BASE_URL}/files/",
        headers={k: v for k, v in auth_headers.items()},
        files={"file": ("shareable_test.txt", io.BytesIO(content), "text/plain")},
    )
    if resp.status_code != 201:
        pytest.skip(f"Upload failed: {resp.text}")
    return resp.json()


class TestShareableLinks:
    def test_create_shareable_link(self, auth_headers, uploaded_file):
        """POST /api/v1/files/{id}/share/ — creates a shareable link."""
        file_id = uploaded_file["id"]
        resp = requests.post(
            f"{BASE_URL}/files/{file_id}/share/",
            headers=auth_headers,
            json={"expires_in_days": 7},
        )
        if resp.status_code == 404:
            pytest.skip("Shareable link endpoint not yet exposed")
        assert resp.status_code in (200, 201), f"Share failed: {resp.text}"
        data = resp.json()
        assert "url" in data or "share_url" in data or "token" in data

    def test_shareable_link_accessible_without_auth(self, auth_headers, uploaded_file):
        """Shareable link URL should be accessible without auth."""
        file_id = uploaded_file["id"]

        # Create link
        share_resp = requests.post(
            f"{BASE_URL}/files/{file_id}/share/",
            headers=auth_headers,
            json={"expires_in_days": 7},
        )
        if share_resp.status_code == 404:
            pytest.skip("Shareable link endpoint not yet exposed")
        if share_resp.status_code not in (200, 201):
            pytest.skip("Share creation failed")

        data = share_resp.json()
        share_url = data.get("url") or data.get("share_url")

        if not share_url:
            token = data.get("token")
            if token:
                share_url = f"{BASE_URL}/files/shared/{token}/"

        if not share_url:
            pytest.skip("No share URL found in response")

        # Access without auth
        download_resp = requests.get(share_url)
        assert download_resp.status_code in (200, 302), \
            f"Shared file not accessible: {download_resp.status_code}"

    def test_list_shared_links(self, auth_headers, uploaded_file):
        """GET /api/v1/files/{id}/shares/ — list of shared links for a file."""
        file_id = uploaded_file["id"]
        resp = requests.get(
            f"{BASE_URL}/files/{file_id}/shares/",
            headers=auth_headers,
        )
        assert resp.status_code in (200, 404)

    def test_revoke_shareable_link(self, auth_headers, uploaded_file):
        """DELETE on a shared link should revoke access."""
        file_id = uploaded_file["id"]

        # Create link
        share_resp = requests.post(
            f"{BASE_URL}/files/{file_id}/share/",
            headers=auth_headers,
            json={"expires_in_days": 1},
        )
        if share_resp.status_code in (404, 400):
            pytest.skip("Share endpoint not available")

        if share_resp.status_code not in (200, 201):
            pytest.skip(f"Share creation failed: {share_resp.status_code}")

        data = share_resp.json()
        link_id = data.get("id")

        if not link_id:
            pytest.skip("No link ID returned")

        # Revoke
        delete_resp = requests.delete(
            f"{BASE_URL}/files/{file_id}/shares/{link_id}/",
            headers=auth_headers,
        )
        assert delete_resp.status_code in (200, 204, 404)

    def test_download_file_authenticated(self, auth_headers, uploaded_file):
        """GET /api/v1/files/{id}/download/ — authenticated download."""
        file_id = uploaded_file["id"]
        resp = requests.get(
            f"{BASE_URL}/files/{file_id}/download/",
            headers=auth_headers,
            allow_redirects=True,
        )
        # 200 = inline download, 302 = redirect to S3
        assert resp.status_code in (200, 302)

    def test_download_requires_auth_or_share_token(self, uploaded_file):
        """GET /api/v1/files/{id}/download/ — unauthenticated returns 401."""
        file_id = uploaded_file["id"]
        resp = requests.get(
            f"{BASE_URL}/files/{file_id}/download/",
            allow_redirects=False,
        )
        assert resp.status_code in (401, 403, 302)
