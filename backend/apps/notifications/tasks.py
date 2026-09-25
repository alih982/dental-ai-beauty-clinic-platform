from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.notifications.models import Notification, EmailNotification
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task
def send_live_notification(user_id, title, message, notification_type='info', link=None):
    """
    Saves a notification to DB and sends it via WebSocket
    """
    try:
        user = User.objects.get(id=user_id)
        
        # 1. Save to Database
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
        
        # 2. Send via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notify_{user_id}",
            {
                "type": "send_notification",
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "link": link,
                "timestamp": notification.created_at.isoformat()
            }
        )
        return f"Notification sent to user {user_id}"
    except Exception as e:
        logger.error(f"Failed to send live notification: {str(e)}")
        return str(e)

@shared_task
def send_email_notification_task(user_id, subject, message, html_message=None):
    """
    Sends an email notification if SMTP is configured
    """
    try:
        user = User.objects.get(id=user_id)
        email = user.email
        
        if not email:
            return "User has no email"
            
        # Check if email is enabled in settings (mock check or from env)
        if not getattr(settings, 'EMAIL_HOST', None) or settings.EMAIL_HOST == 'maggicaihub.com':
            # Save as pending/log but don't send if not configured
            EmailNotification.objects.create(
                user=user,
                subject=subject,
                message=message,
                html_message=html_message,
                status='pending',
                error_message="SMTP not configured"
            )
            return "SMTP not configured, skipping send"

        # Send actual email
        EmailNotification.objects.create(
            user=user,
            subject=subject,
            message=message,
            html_message=html_message,
            status='sent',
            sent_at=timezone.now()
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        return f"Email sent to {email}"
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return str(e)
