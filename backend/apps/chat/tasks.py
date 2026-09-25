"""
Celery tasks for chat functionality.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_chat_notification(self, user_id, sender_name, message_preview):
    """
    Send notification for new chat message.
    This is already handled in consumers.py but can be used as backup.
    """
    try:
        from apps.notifications.models import Notification
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        Notification.objects.create(
            user=user,
            title=f"New message from {sender_name}",
            message=message_preview[:100] if len(message_preview) > 100 else message_preview,
            notification_type='message',
            link='/dashboard/messages'
        )
        logger.info(f"Chat notification sent to user {user_id}")
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found for chat notification")
    except Exception as exc:
        logger.error(f"Error sending chat notification: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_old_chat_sessions():
    """
    Clean up old chat sessions and messages.
    Run daily to keep database healthy.
    """
    from apps.chat.models import Message, Conversation
    
    try:
        # Delete messages older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_messages = Message.objects.filter(timestamp__lt=cutoff_date).delete()
        logger.info(f"Cleaned up {deleted_messages[0]} old messages")
        
        # Delete conversations with no messages
        empty_conversations = Conversation.objects.annotate(
            msg_count=models.Count('messages')
        ).filter(msg_count=0, updated_at__lt=cutoff_date).delete()
        logger.info(f"Cleaned up {empty_conversations[0]} empty conversations")
        
        return {
            'messages_deleted': deleted_messages[0],
            'conversations_deleted': empty_conversations[0]
        }
    except Exception as e:
        logger.error(f"Error in cleanup_old_chat_sessions: {e}")
        return {'error': str(e)}


@shared_task
def generate_chat_analytics():
    """
    Generate daily chat analytics.
    Run daily to track chat usage.
    """
    from apps.chat.models import Message, Conversation
    from django.contrib.auth import get_user_model
    from django.db.models import Count
    
    try:
        today = timezone.now().date()
        
        # Count messages today
        messages_today = Message.objects.filter(timestamp__date=today).count()
        
        # Count conversations created today
        conversations_today = Conversation.objects.filter(created_at__date=today).count()
        
        # Count active conversations (updated in last 24 hours)
        active_conversations = Conversation.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        
        # Most active users
        most_active_users = Message.objects.filter(
            timestamp__date=today
        ).values('sender__phone_number').annotate(
            msg_count=Count('id')
        ).order_by('-msg_count')[:10]
        
        analytics = {
            'date': str(today),
            'messages_count': messages_today,
            'conversations_created': conversations_today,
            'active_conversations': active_conversations,
            'most_active_users': list(most_active_users)
        }
        
        logger.info(f"Chat analytics generated: {analytics}")
        return analytics
    except Exception as e:
        logger.error(f"Error generating chat analytics: {e}")
        return {'error': str(e)}


@shared_task(bind=True, max_retries=3)
def queue_ai_response(self, conversation_id, user_message, user_id=None):
    """
    Queue AI response generation for better performance.
    The actual AI response is handled in real-time via WebSocket,
    but this can be used for logging or follow-up actions.
    """
    try:
        from apps.chat.models import Conversation, Message
        from apps.ai_orchestrator.services import AIService
        
        # This is a placeholder - the actual AI response is streaming
        # via WebSocket in consumers.py
        logger.info(f"AI response queued for conversation {conversation_id}")
        
        return {
            'status': 'queued',
            'conversation_id': conversation_id,
            'user_message': user_message[:50]
        }
    except Exception as exc:
        logger.error(f"Error in queue_ai_response: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task
def mark_messages_as_read(conversation_id, user_id):
    """
    Mark all messages in a conversation as read for a specific user.
    """
    try:
        from apps.chat.models import Message
        
        # Mark messages from the other participant as read
        updated_count = Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender_id=user_id).update(is_read=True)
        
        logger.info(f"Marked {updated_count} messages as read in conversation {conversation_id}")
        return {'updated_count': updated_count}
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        return {'error': str(e)}


# Import needed for cleanup task
from django.db import models

