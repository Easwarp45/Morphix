"""
Morphix â€” Conversion URLs
"""

from django.urls import path

from .views import (
    ConversionCreateView,
    ConversionDetailView,
    ConversionDownloadView,
    ConversionListView,
    SupportedFormatsView,
    BatchConversionCreateView,
    BatchConversionStatusView,
    BatchZipCreateView,
    CreateDownloadShareView,
    PublicDownloadShareView,
)

urlpatterns = [
    path("", ConversionCreateView.as_view(), name="conversion-create"),
    path("list/", ConversionListView.as_view(), name="conversion-list"),
    path("batch/", BatchConversionCreateView.as_view(), name="batch-conversion-create"),
    path("batch/<uuid:batch_id>/", BatchConversionStatusView.as_view(), name="batch-conversion-status"),
    path("batch/<uuid:batch_id>/zip/", BatchZipCreateView.as_view(), name="batch-zip-create"),
    path("<uuid:pk>/", ConversionDetailView.as_view(), name="conversion-detail"),
    path("<uuid:pk>/download/", ConversionDownloadView.as_view(), name="conversion-download"),
    path("<uuid:pk>/share/", CreateDownloadShareView.as_view(), name="conversion-share"),
    path("share/<str:token>/", PublicDownloadShareView.as_view(), name="public-share-download"),
    path("formats/", SupportedFormatsView.as_view(), name="supported-formats"),
]
