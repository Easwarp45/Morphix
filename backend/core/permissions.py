"""
Cloud File Converter — Custom Permissions
"""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Allows access only to admin/staff users."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsOwner(BasePermission):
    """Allows access only to the owner of the object."""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "user_id"):
            return obj.user_id == request.user.id
        return False


class IsOwnerOrAdmin(BasePermission):
    """Allows access to the owner or admin users."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "user_id"):
            return obj.user_id == request.user.id
        return False
