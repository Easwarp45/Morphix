"""
Cloud File Converter — Admin Panel URLs
"""

from django.urls import path

from .views import (
    AdminAnalyticsView,
    AdminDeactivateUserView,
    AdminStorageMonitorView,
    AdminUserDetailView,
    AdminUserListView,
)

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<uuid:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("users/<uuid:pk>/deactivate/", AdminDeactivateUserView.as_view(), name="admin-user-deactivate"),
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("storage/", AdminStorageMonitorView.as_view(), name="admin-storage"),
]
