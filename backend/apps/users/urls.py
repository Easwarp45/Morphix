"""
Morphix â€” User URLs
"""

from django.urls import path
from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView, LogoutView, PasswordResetConfirmView, PasswordResetView
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    ChangePasswordView,
    DeleteAccountView,
    GoogleLoginView,
    UserProfileView,
    GuestAuthView,
)

urlpatterns = [
    # Registration & Login
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("guest/", GuestAuthView.as_view(), name="auth-guest"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),

    # JWT Token management
    path("token/refresh/", get_refresh_view().as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),

    # Password management
    path("password/reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),

    # Google OAuth
    path("google/", GoogleLoginView.as_view(), name="google-login"),

    # User profile
    path("user/", UserProfileView.as_view(), name="user-profile"),
    path("user/delete/", DeleteAccountView.as_view(), name="user-delete"),
]
