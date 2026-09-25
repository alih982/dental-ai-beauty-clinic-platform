from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatStreamView, ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')
router.register(r'messages', MessageViewSet, basename='messages')

urlpatterns = [
    path('', include(router.urls)),
    path('stream/', ChatStreamView.as_view(), name='chat_stream'),
]
