"""
Morphix â€” Analytics URLs
"""

from django.urls import path

from .views import ConversionHistoryView, DashboardStatsView, UsageStatsView

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("history/", ConversionHistoryView.as_view(), name="conversion-history"),
    path("usage/", UsageStatsView.as_view(), name="usage-stats"),
]
