"""
ASGI config for Smart Health Platform.
Enables WebSocket support via Django Channels.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Use production settings by default, can be overridden by environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.production'))

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import routing after Django initialization
from config.routing import websocket_urlpatterns, websocket_urlpatterns_fallback
from config.middleware import TokenAuthMiddlewareStack

# Combine all websocket patterns
all_websocket_urlpatterns = websocket_urlpatterns + websocket_urlpatterns_fallback

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddlewareStack(
            URLRouter(all_websocket_urlpatterns)
        )
    ),
})
