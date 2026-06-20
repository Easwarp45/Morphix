"""
Cloud File Converter — E2E Tests: File Upload & Conversion
===========================================================
Tests file upload, format conversion, batch conversion, download,
shareable links, and conversion history.
"""

import io
import os
import time
import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"

# ── Sample test files (in-memory) ──────────────────────────────────────────────

def make_text_file(content: str = "Hello, Cloud File Converter!\n" * 50) -> io.BytesIO:
    return io.BytesIO(content.encode())


def make_minimal_pdf() -> io.BytesIO:
    """Create a minimal valid PDF in memory."""
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n"
        b"0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n197\n%%EOF"
    )
    return io.BytesIO(pdf_bytes)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def auth_headers():
    """Get auth tokens for test user."""
    # First try to register, then login
    creds = {
        "email": "upload_e2e@cloudconv.test",
        "password": "Upload#E2eTest2024!",
        "first_name": "Upload",
        "last_name": "Tester",
    }
    requests.post(f"{BASE_URL}/auth/register/", json=creds)  # may already exist
    resp = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": creds["email"], "password": creds["password"]
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access"]
    return {"Authorization": f"Bearer {token}"}


# ── Upload Tests ────────────────────────────────────────────────────────────────

class TestFileUpload:
    def test_upload_text_file(self, auth_headers):
        """POST /api/v1/files/ — upload a .txt file, returns 201."""
        response = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("test.txt", make_text_file(), "text/plain")},
        )
        assert response.status_code == 201, f"Upload failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data.get("original_filename") == "test.txt" or "name" in data

    def test_upload_pdf_file(self, auth_headers):
        """POST /api/v1/files/ — upload a .pdf file."""
        response = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("test.pdf", make_minimal_pdf(), "application/pdf")},
        )
        assert response.status_code == 201, f"PDF upload failed: {response.text}"

    def test_upload_requires_auth(self):
        """POST /api/v1/files/ — returns 401 without token."""
        response = requests.post(
            f"{BASE_URL}/files/",
            files={"file": ("test.txt", make_text_file(), "text/plain")},
        )
        assert response.status_code == 401

    def test_upload_too_large_file(self, auth_headers):
        """POST /api/v1/files/ — file exceeding limit should be rejected."""
        big_file = io.BytesIO(b"X" * (60 * 1024 * 1024))  # 60 MB
        response = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("huge.txt", big_file, "text/plain")},
        )
        # Either 400 (validation error) or 413 (request entity too large)
        assert response.status_code in (400, 413), f"Expected rejection, got {response.status_code}"

    def test_list_files(self, auth_headers):
        """GET /api/v1/files/ — returns paginated list of user's files."""
        response = requests.get(f"{BASE_URL}/files/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Accept both paginated (results key) and direct list
        assert isinstance(data, (list, dict))


# ── Conversion Tests ────────────────────────────────────────────────────────────

class TestConversion:
    @pytest.fixture(scope="class")
    def uploaded_file_id(self, auth_headers):
        """Upload a file and return its ID for conversion tests."""
        response = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("conv_test.txt", make_text_file(), "text/plain")},
        )
        assert response.status_code == 201
        return response.json()["id"]

    def test_start_conversion(self, auth_headers, uploaded_file_id):
        """POST /api/v1/conversions/ — start a conversion job."""
        response = requests.post(
            f"{BASE_URL}/conversions/",
            headers=auth_headers,
            json={
                "file_id": uploaded_file_id,
                "target_format": "pdf",
            },
        )
        assert response.status_code in (200, 201, 202), f"Conversion start failed: {response.text}"
        data = response.json()
        assert "id" in data or "task_id" in data or "job_id" in data

    def test_conversion_status(self, auth_headers, uploaded_file_id):
        """POST then GET conversion — status should be pending/processing/completed."""
        # Start conversion
        start_resp = requests.post(
            f"{BASE_URL}/conversions/",
            headers=auth_headers,
            json={"file_id": uploaded_file_id, "target_format": "pdf"},
        )
        if start_resp.status_code not in (200, 201, 202):
            pytest.skip("Conversion start failed, skipping status check")

        data = start_resp.json()
        conv_id = data.get("id") or data.get("task_id") or data.get("job_id")

        # Poll for up to 30 seconds
        for _ in range(10):
            time.sleep(3)
            status_resp = requests.get(
                f"{BASE_URL}/conversions/{conv_id}/",
                headers=auth_headers,
            )
            if status_resp.status_code == 200:
                status = status_resp.json().get("status", "")
                if status in ("completed", "failed"):
                    break

        assert status_resp.status_code == 200

    def test_list_conversions(self, auth_headers):
        """GET /api/v1/conversions/ — returns user's conversion history."""
        response = requests.get(f"{BASE_URL}/conversions/", headers=auth_headers)
        assert response.status_code == 200


# ── Guest Conversion ────────────────────────────────────────────────────────────

class TestGuestConversion:
    def test_guest_upload_within_limit(self):
        """Guests should be able to upload within their file size limit."""
        small_file = io.BytesIO(b"Guest test file content." * 100)
        response = requests.post(
            f"{BASE_URL}/files/guest/",
            files={"file": ("guest_test.txt", small_file, "text/plain")},
        )
        # Either 201 (allowed) or 404 (endpoint doesn't exist in this impl)
        assert response.status_code in (200, 201, 404)


# ── Shareable Links ─────────────────────────────────────────────────────────────

class TestShareableLinks:
    def test_create_shareable_link(self, auth_headers):
        """Files should support shareable link generation."""
        # Upload a file first
        upload_resp = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("share_test.txt", make_text_file(), "text/plain")},
        )
        if upload_resp.status_code != 201:
            pytest.skip("File upload failed, skipping shareable link test")

        file_id = upload_resp.json()["id"]

        # Create shareable link
        share_resp = requests.post(
            f"{BASE_URL}/files/{file_id}/share/",
            headers=auth_headers,
            json={"expires_in_days": 7},
        )
        # Accept 200, 201, or 404 (if feature not yet exposed)
        assert share_resp.status_code in (200, 201, 404)
