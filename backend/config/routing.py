from django.urls import re_path
from apps.chat import consumers as chat_consumers
from apps.notifications import consumers as notification_consumers

# Import appointment websocket consumers with error handling
try:
    from apps.appointments.websocket import consumers as appointment_websocket_consumers
    APPOINTMENT_WS_AVAILABLE = True
except ImportError:
    APPOINTMENT_WS_AVAILABLE = False
    appointment_websocket_consumers = None

websocket_urlpatterns = [
    re_path(r'ws/chat/$', chat_consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', notification_consumers.NotificationConsumer.as_asgi()),
]

# Add fallback routes without trailing slash for compatibility
websocket_urlpatterns_fallback = [
    re_path(r'ws/chat$', chat_consumers.ChatConsumer.as_asgi()),
]

# Add appointment websocket if available
if APPOINTMENT_WS_AVAILABLE and hasattr(appointment_websocket_consumers, 'AIAssistantConsumer'):
    websocket_urlpatterns.append(
        re_path(r'ws/appointment/ai/$', appointment_websocket_consumers.AIAssistantConsumer.as_asgi()),
    )
