"""
Cloud File Converter — User Serializers
"""

from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

from .models import User


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user profile details."""

    full_name = serializers.CharField(read_only=True)
    storage_usage_percent = serializers.FloatField(read_only=True)
    storage_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar_url",
            "auth_provider",
            "is_guest",
            "storage_used",
            "storage_limit",
            "storage_remaining",
            "storage_usage_percent",
            "is_staff",
            "created_at",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",
            "auth_provider",
            "is_guest",
            "storage_used",
            "storage_limit",
            "is_staff",
            "created_at",
            "last_login",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar_url"]


class CustomRegisterSerializer(RegisterSerializer):
    """Extended registration serializer with first/last name."""

    username = None  # Remove username field
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["first_name"] = self.validated_data.get("first_name", "")
        data["last_name"] = self.validated_data.get("last_name", "")
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.save(update_fields=["first_name", "last_name"])
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    """Admin view of user details."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar_url",
            "auth_provider",
            "is_guest",
            "is_active",
            "is_staff",
            "storage_used",
            "storage_limit",
            "created_at",
            "last_login",
        ]
