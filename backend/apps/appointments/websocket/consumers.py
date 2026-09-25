"""
WebSocket Consumer for AI Assistant
Connects Django Channels to FastAPI AI service streaming
"""
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import aiohttp
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AIAssistantConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time AI chat.
    
    Flow:
    1. Frontend connects via WebSocket
    2. Frontend sends message
    3. Consumer forwards to FastAPI AI service
    4. Stream AI response back to frontend via SSE format
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = None

    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        logger.info("AI Assistant WebSocket connected")
    
    async def disconnect(self, close_code):
        """Cleanup on disconnect"""
        if self.session:
            await self.session.close()
        logger.info(f"AI Assistant WebSocket disconnected: {close_code}")
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        """
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            conversation_id = data.get('conversation_id')
            
            if not message:
                await self.send(text_data=json.dumps({
                    'error': 'پیام خالی است'
                }))
                return
            
            # Create session if not exists
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()
            
            # Get AI service URL from settings
            ai_service_url = getattr(settings, 'AI_SERVICE_URL', 'http://ai_service:8001')
            stream_url = f"{ai_service_url}/api/v1/chat/stream"
            
            async with self.session.post(
                stream_url,
                json={
                    'message': message,
                    'conversation_id': conversation_id
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    await self.send(text_data=json.dumps({
                        'error': f'خطا در ارتباط با سرویس هوش مصنوعی: {response.status}'
                    }))
                    return

                # Stream response back to client
                async for chunk in response.content.iter_any():
                    if chunk:
                        # Forward raw chunks or parse SSE line by line
                        # For simplicity and performance, we forward as they come
                        # but ensure they are decoded correctly if needed
                        await self.send(text_data=chunk.decode('utf-8'))
        
        except aiohttp.ClientError as e:
            logger.error(f"AI Service connection error: {e}")
            await self.send(text_data=json.dumps({'error': 'سرویس هوش مصنوعی در دسترس نیست'}))
        except Exception as e:
            logger.error(f"Error in WebSocket consumer: {e}", exc_info=True)
            await self.send(text_data=json.dumps({'error': 'خطای داخلی سرور'}))
