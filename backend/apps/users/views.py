"""
Cloud File Converter — User Views
"""

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserDetailSerializer,
    UserUpdateSerializer,
)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update the authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserDetailSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full profile after update
        return Response(
            {
                "success": True,
                "data": UserDetailSerializer(instance).data,
            }
        )


class GoogleLoginView(SocialLoginView):
    """Handle Google OAuth2 login / registration."""

    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:5173/auth/google/callback"
    client_class = OAuth2Client


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Both old_password and new_password are required.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "invalid_password",
                        "message": "Current password is incorrect.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "New password must be at least 8 characters.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {
                "success": True,
                "data": {"message": "Password changed successfully."},
            }
        )


class DeleteAccountView(APIView):
    """Delete (deactivate) the authenticated user's account."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(
            {
                "success": True,
                "data": {"message": "Account deactivated successfully."},
            }
        )


class GuestAuthView(APIView):
    """Create a temporary guest user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = User.objects.create_guest()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "is_guest": True,
                    },
                },
            },
            status=status.HTTP_201_CREATED,
        )
