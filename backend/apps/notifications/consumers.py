import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        
        # Allow both authenticated and anonymous users
        self.is_anonymous = not self.user or not hasattr(self.user, 'is_authenticated') or not self.user.is_authenticated
        
        if self.is_anonymous:
            # Allow guests to connect for notifications (read-only)
            logger.info("Anonymous user connecting to notifications")
        else:
            # Personal notification group for each authenticated user
            self.notification_group_name = f"notify_{self.user.id}"

            # Join personal notification group
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} connected to notifications")

        await self.accept()

    async def disconnect(self, close_code):
        # Leave personal notification group only if authenticated
        if not self.is_anonymous and hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
        logger.info(f"Notification WebSocket disconnected with code: {close_code}")

    async def send_notification(self, event):
        """
        Send notification event to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': event.get('notification_type', 'info'),
            'title': event.get('title'),
            'message': event.get('message'),
            'link': event.get('link'),
            'timestamp': event.get('timestamp'),
        }))
