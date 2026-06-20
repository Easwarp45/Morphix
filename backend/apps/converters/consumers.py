"""
Morphix â€” WebSocket Consumers
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class ConversionConsumer(AsyncJsonWebsocketConsumer):
    """Consumer for receiving real-time conversion progress updates."""

    async def connect(self):
        query_params = parse_qs(self.scope["query_string"].decode())
        token_list = query_params.get("token", [])

        self.user = None
        if token_list:
            token = token_list[0]
            self.user = await self.get_user_from_token(token)

        if self.user is None or not self.user.is_active:
            # Reject connection if unauthorized
            await self.close(code=4001)
            return

        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception:
            return None

    async def conversion_update(self, event):
        """Receive update message from group and send to WebSocket."""
        await self.send_json(event["data"])
