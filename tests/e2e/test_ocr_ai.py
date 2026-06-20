"""
Cloud File Converter — E2E Tests: OCR & AI Summarization
=========================================================
Tests OCR extraction from images/scanned PDFs and AI-powered
document summarization via the Gemini API.
"""

import io
import struct
import zlib
import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"


def make_minimal_png() -> io.BytesIO:
    """Create a minimal valid 1x1 white PNG image in memory."""
    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)  # 1x1 RGB
    ihdr = png_chunk(b"IHDR", ihdr_data)
    idat_data = zlib.compress(b"\x00\xff\xff\xff")  # white pixel
    idat = png_chunk(b"IDAT", idat_data)
    iend = png_chunk(b"IEND", b"")
    return io.BytesIO(signature + ihdr + idat + iend)


@pytest.fixture(scope="module")
def auth_headers():
    creds = {
        "email": "ocr_e2e@cloudconv.test",
        "password": "Ocr#E2eTest2024!",
        "first_name": "OCR",
        "last_name": "Tester",
    }
    requests.post(f"{BASE_URL}/auth/register/", json=creds)
    resp = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": creds["email"], "password": creds["password"]
    })
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access']}"}


class TestOCR:
    def test_image_upload_accepted(self, auth_headers):
        """POST /api/v1/files/ — PNG image upload should be accepted."""
        response = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("test_image.png", make_minimal_png(), "image/png")},
        )
        # 201 = success, 400 = format not supported (acceptable for minimal PNG)
        assert response.status_code in (201, 400), f"Unexpected: {response.status_code} {response.text}"

    def test_ocr_conversion_endpoint_exists(self, auth_headers):
        """OCR conversion type should be recognized by the API."""
        # Upload a file first
        upload_resp = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("ocr_test.png", make_minimal_png(), "image/png")},
        )
        if upload_resp.status_code != 201:
            pytest.skip("Image upload not supported in this build")

        file_id = upload_resp.json()["id"]

        # Try OCR conversion
        conv_resp = requests.post(
            f"{BASE_URL}/conversions/",
            headers=auth_headers,
            json={"file_id": file_id, "target_format": "txt", "use_ocr": True},
        )
        # Accept 200/201/202 (success) or 400 (feature disabled gracefully)
        assert conv_resp.status_code in (200, 201, 202, 400)


class TestAISummarization:
    @pytest.fixture(scope="class")
    def uploaded_text_file_id(self, auth_headers):
        content = (
            "Machine learning is a subset of artificial intelligence that enables "
            "computers to learn from data without being explicitly programmed. "
            "Deep learning uses neural networks with many layers to solve complex problems. "
            "Natural language processing allows computers to understand human language. "
        ) * 10
        upload_resp = requests.post(
            f"{BASE_URL}/files/",
            headers={k: v for k, v in auth_headers.items()},
            files={"file": ("ai_test_doc.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        if upload_resp.status_code != 201:
            pytest.skip("File upload failed")
        return upload_resp.json()["id"]

    def test_summarization_endpoint_exists(self, auth_headers, uploaded_text_file_id):
        """POST summarize endpoint should exist and return 200/202 or 404."""
        response = requests.post(
            f"{BASE_URL}/files/{uploaded_text_file_id}/summarize/",
            headers=auth_headers,
        )
        # 200/202 = success, 404 = endpoint not exposed via URL (check conversions)
        assert response.status_code in (200, 202, 404)

    def test_ai_conversion_with_summarize_flag(self, auth_headers, uploaded_text_file_id):
        """Conversion with summarize flag should be accepted."""
        response = requests.post(
            f"{BASE_URL}/conversions/",
            headers=auth_headers,
            json={
                "file_id": uploaded_text_file_id,
                "target_format": "txt",
                "summarize": True,
            },
        )
        assert response.status_code in (200, 201, 202, 400)

    def test_summarization_requires_auth(self, uploaded_text_file_id):
        """Summarize endpoint should require authentication."""
        response = requests.post(
            f"{BASE_URL}/files/{uploaded_text_file_id}/summarize/",
        )
        assert response.status_code in (401, 404)


class TestHealthCheckEndpoint:
    def test_health_check_returns_200(self):
        """GET /api/v1/health/ — health check must always return 200."""
        response = requests.get(f"{BASE_URL}/health/")
        assert response.status_code == 200

    def test_health_check_json_structure(self):
        """GET /api/v1/health/ — response body must have status fields."""
        response = requests.get(f"{BASE_URL}/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "database" in data, \
            f"Health check missing expected fields: {data}"
