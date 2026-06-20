"""
Morphix â€” Centralized Exception Handling
"""

import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


# =============================================================================
# Custom API Exceptions
# =============================================================================


class FileConversionError(APIException):
    """Raised when a file conversion fails."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "File conversion failed."
    default_code = "conversion_error"


class FileTooLargeError(APIException):
    """Raised when uploaded file exceeds size limit."""

    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "File size exceeds the maximum allowed limit."
    default_code = "file_too_large"


class UnsupportedFormatError(APIException):
    """Raised when file format is not supported."""

    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "File format is not supported."
    default_code = "unsupported_format"


class StorageLimitExceededError(APIException):
    """Raised when user's storage quota is exceeded."""

    status_code = status.HTTP_507_INSUFFICIENT_STORAGE
    default_detail = "Storage limit exceeded."
    default_code = "storage_limit_exceeded"


class ConversionInProgressError(APIException):
    """Raised when trying to delete a file that's being converted."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cannot delete file while conversion is in progress."
    default_code = "conversion_in_progress"


# =============================================================================
# Custom Exception Handler
# =============================================================================


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps all errors in a consistent format:

    {
        "success": false,
        "error": {
            "code": "error_code",
            "message": "Human-readable message",
            "details": { ... }
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, "default_code", "error")
        if isinstance(response.data, dict):
            detail = response.data.get("detail", str(exc))
            details = {
                k: v for k, v in response.data.items() if k != "detail"
            }
        elif isinstance(response.data, list):
            detail = response.data[0] if response.data else str(exc)
            details = {}
        else:
            detail = str(response.data)
            details = {}

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": str(detail),
                **({"details": details} if details else {}),
            },
        }
    else:
        # Unhandled exception â€” log and return 500
        logger.exception("Unhandled exception in %s", context.get("view", "unknown"))
        return Response(
            {
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
