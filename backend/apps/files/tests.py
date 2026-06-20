"""
Morphix â€” Files App Tests
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.files.models import File
from apps.files.services import FileService


# =============================================================================
# Model Tests
# =============================================================================

def test_file_model_properties():
    # We do not use database for unit testing model helper properties
    file_record = File(
        original_name="test.png",
        mime_type="image/png",
        file_extension=".png",
        file_size=1024 * 1024 * 2,  # 2 MB
    )
    assert file_record.file_size_mb == 2.0
    assert file_record.is_image is True
    assert file_record.is_document is False

    doc_record = File(
        original_name="report.pdf",
        mime_type="application/pdf",
        file_extension=".pdf",
        file_size=512 * 1024,  # 0.5 MB
    )
    assert doc_record.file_size_mb == 0.5
    assert doc_record.is_image is False
    assert doc_record.is_document is True


# =============================================================================
# Service & API Tests
# =============================================================================

@pytest.mark.django_db
class TestFileOperations:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        # Mock the entire StorageService to prevent actual AWS connection
        self.storage_mock = MagicMock()
        self.storage_mock.generate_s3_key.return_value = "uploads/user1/test.png"
        self.storage_mock.upload_file.return_value = True
        self.storage_mock.delete_file.return_value = True

        self.storage_patcher = patch("apps.files.services.get_storage_service", return_value=self.storage_mock)
        self.storage_patcher.start()
        yield
        self.storage_patcher.stop()

    def test_upload_file_service_success(self, user):
        uploaded_file = SimpleUploadedFile(
            "test.png", b"file_content", content_type="image/png"
        )
        
        file_record = FileService.upload_file(user, uploaded_file)
        
        assert file_record.original_name == "test.png"
        assert file_record.file_size == len(b"file_content")
        assert file_record.status == File.Status.UPLOADED
        assert user.storage_used == len(b"file_content")
        self.storage_mock.upload_file.assert_called_once()

    def test_upload_file_exceeds_max_size(self, user):
        large_file = SimpleUploadedFile(
            "large.pdf", b"a" * (settings.USER_MAX_UPLOAD_SIZE + 100), content_type="application/pdf"
        )
        with pytest.raises(Exception, match="exceeds maximum allowed"):
            FileService.upload_file(user, large_file)

    def test_upload_file_exceeds_guest_max_size(self, user):
        user.is_guest = True
        large_file = SimpleUploadedFile(
            "large.pdf", b"a" * (settings.GUEST_MAX_UPLOAD_SIZE + 100), content_type="application/pdf"
        )
        with pytest.raises(Exception, match="exceeds maximum allowed"):
            FileService.upload_file(user, large_file)

    def test_upload_file_unsupported_format(self, user):
        bad_file = SimpleUploadedFile(
            "script.sh", b"echo 'hello'", content_type="text/x-shellscript"
        )
        with pytest.raises(Exception, match="not supported"):
            FileService.upload_file(user, bad_file)

    def test_upload_file_storage_limit_exceeded(self, user):
        # Set limit very low
        user.storage_limit = 100
        user.save()
        
        uploaded_file = SimpleUploadedFile(
            "test.png", b"a" * 150, content_type="image/png"
        )
        with pytest.raises(Exception, match="exceeded your storage limit"):
            FileService.upload_file(user, uploaded_file)

    def test_delete_file_service(self, user):
        uploaded_file = SimpleUploadedFile(
            "test.png", b"content", content_type="image/png"
        )
        file_record = FileService.upload_file(user, uploaded_file)
        initial_storage = user.storage_used

        FileService.delete_file(file_record)

        assert file_record.status == File.Status.DELETED
        assert user.storage_used == initial_storage - len(b"content")
        self.storage_mock.delete_file.assert_called_once_with(file_record.s3_key)


@pytest.mark.django_db
class TestFileAPIEndpoints:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.storage_mock = MagicMock()
        self.storage_mock.generate_s3_key.return_value = "uploads/user1/test.png"
        self.storage_mock.upload_file.return_value = True
        self.storage_mock.delete_file.return_value = True

        self.storage_patcher = patch("apps.files.services.get_storage_service", return_value=self.storage_mock)
        self.storage_patcher.start()
        yield
        self.storage_patcher.stop()

    def test_upload_endpoint_authenticated(self, auth_client):
        file_content = b"fake-image-bytes"
        fp = io.BytesIO(file_content)
        fp.name = "test.png"
        
        response = auth_client.post(
            "/api/v1/files/upload/",
            {"files": [fp]},
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert len(response.data["data"]["uploaded"]) == 1
        assert response.data["data"]["uploaded"][0]["original_name"] == "test.png"

    def test_upload_endpoint_unauthenticated(self, api_client):
        fp = io.BytesIO(b"data")
        fp.name = "test.png"
        response = api_client.post(
            "/api/v1/files/upload/",
            {"files": [fp]},
            format="multipart",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_files(self, auth_client, user):
        # Create some files
        File.objects.create(
            user=user,
            original_name="f1.png",
            stored_name="s1.png",
            s3_key="k1",
            mime_type="image/png",
            file_extension=".png",
            file_size=100,
        )
        File.objects.create(
            user=user,
            original_name="f2.pdf",
            stored_name="s2.pdf",
            s3_key="k2",
            mime_type="application/pdf",
            file_extension=".pdf",
            file_size=200,
        )

        response = auth_client.get("/api/v1/files/")
        assert response.status_code == status.HTTP_200_OK
        # Check standard pagination wrap if any or list
        if "data" in response.data:
            results = response.data["data"]
        elif "results" in response.data:
            results = response.data["results"]
        else:
            results = response.data
        assert len(results) == 2

    def test_retrieve_file(self, auth_client, user):
        file_record = File.objects.create(
            user=user,
            original_name="f1.png",
            stored_name="s1.png",
            s3_key="k1",
            mime_type="image/png",
            file_extension=".png",
            file_size=100,
        )
        response = auth_client.get(f"/api/v1/files/{file_record.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["original_name"] == "f1.png"

    def test_delete_file(self, auth_client, user):
        file_record = File.objects.create(
            user=user,
            original_name="f1.png",
            stored_name="s1.png",
            s3_key="k1",
            mime_type="image/png",
            file_extension=".png",
            file_size=100,
        )
        response = auth_client.delete(f"/api/v1/files/{file_record.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert File.objects.get(id=file_record.id).status == File.Status.DELETED
