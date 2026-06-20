"""
Cloud File Converter — WebSocket Routing
"""

from django.urls import re_path

from .consumers import ConversionConsumer

websocket_urlpatterns = [
    re_path(r"ws/conversions/$", ConversionConsumer.as_asgi()),
]
