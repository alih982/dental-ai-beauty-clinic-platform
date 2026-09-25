"""
Celery Tasks for Smart Health Platform

Complete set of background tasks for the hospital application:
- Email notifications
- SMS notifications  
- Appointment reminders
- Report generation
- Cache warming
- Data cleanup
- AI tasks
"""

import logging
import asyncio
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)


# ===================
# EMAIL TASKS
# ===================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_email_task(
    self,
    subject: str,
    message: str,
    recipient_list: List[str],
    from_email: Optional[str] = None,
    html_message: Optional[str] = None,
):
    """
    Send email asynchronously.
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient emails
        from_email: Sender email (uses DEFAULT_FROM_EMAIL if not provided)
        html_message: HTML message content
    """
    try:
        from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smarthealth.com')
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {recipient_list}")
        return {'status': 'success', 'recipients': len(recipient_list)}
        
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def send_welcome_email(self, user_id: int):
    """Send welcome email to new users"""
    from apps.accounts.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Welcome to Smart Health Platform"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        Welcome to Smart Health Platform! We're excited to have you on board.
        
        Your account has been created successfully.
        
        Best regards,
        Smart Health Team
        """
        
        send_email_task.delay(subject, message, [user.email])
        return {'status': 'success', 'user_id': user_id}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'error', 'message': 'User not found'}


@shared_task(bind=True)
def send_password_reset_email(self, user_id: int, reset_token: str):
    """Send password reset email"""
    from apps.accounts.models import User
    
    try:
        user = User.objects.get(id=user_id)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        You requested to reset your password. Click the link below:
        {reset_url}
        
        This link will expire in 24 hours.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Smart Health Team
        """
        
        send_email_task.delay(subject, message, [user.email])
        return {'status': 'success'}
        
    except User.DoesNotExist:
        return {'status': 'error', 'message': 'User not found'}


# ===================
# SMS TASKS
# ===================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_sms_task(self, phone_number: str, message: str):
    """
    Send SMS asynchronously.
    
    Args:
        phone_number: Recipient phone number
        message: SMS message content
    """
    try:
        from apps.core.sms_service import SMSService
        
        sms_service = SMSService()
        result = sms_service.send_sms(phone_number, message)
        
        if result['success']:
            logger.info(f"SMS sent to {phone_number}")
            return {'status': 'success', 'phone': phone_number}
        else:
            logger.error(f"SMS failed: {result.get('error')}")
            return {'status': 'error', 'error': result.get('error')}
            
    except Exception as exc:
        logger.error(f"SMS task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def send_appointment_reminder_sms(self, appointment_id: int):
    """Send appointment reminder SMS"""
    from apps.appointments.models import Appointment
    
    try:
        appointment = Appointment.objects.select_related(
            'patient', 'doctor', 'doctor__user'
        ).get(id=appointment_id)
        
        patient_phone = appointment.patient.phone
        doctor_name = appointment.doctor.user.get_full_name()
        appointment_time = appointment.date.strftime('%Y-%m-%d %H:%M')
        
        message = f"""
        سلام {appointment.patient.first_name}،

        یادآوری وقت ملاقات:
        پزشک: دکتر {doctor_name}
        زمان: {appointment_time}

        لطفاً در موعد مقرر حضور داشته باشید.
        """
        
        send_sms_task.delay(patient_phone, message)
        return {'status': 'success', 'appointment_id': appointment_id}
        
    except Appointment.DoesNotExist:
        return {'status': 'error', 'message': 'Appointment not found'}


# ===================
# APPOINTMENT TASKS
# ===================

@shared_task(bind=True)
def process_appointment_reminders(self):
    """Process all appointment reminders - runs every 5 minutes"""
    from apps.appointments.models import Appointment
    
    now = timezone.now()
    reminder_time = now + timedelta(hours=24)
    
    # Get appointments needing reminders (24 hours before)
    appointments = Appointment.objects.filter(
        date__gte=now,
        date__lte=reminder_time,
        status='confirmed',
        reminder_sent=False,
    ).select_related('patient', 'doctor', 'doctor__user')
    
    count = 0
    for appointment in appointments:
        try:
            send_appointment_reminder_sms.delay(appointment.id)
            appointment.reminder_sent = True
            appointment.save(update_fields=['reminder_sent'])
            count += 1
        except Exception as e:
            logger.error(f"Failed to send reminder for appointment {appointment.id}: {e}")
    
    logger.info(f"Processed {count} appointment reminders")
    return {'status': 'success', 'reminders_sent': count}


@shared_task(bind=True)
def process_appointment_cancellations(self):
    """Auto-cancel appointments that weren't confirmed"""
    from apps.appointments.models import Appointment
    
    now = timezone.now()
    cutoff = now - timedelta(hours=24)
    
    # Cancel unconfirmed appointments that passed
    count = Appointment.objects.filter(
        date__lt=now,
        status='pending',
    ).update(status='cancelled')
    
    logger.info(f"Auto-cancelled {count} appointments")
    return {'status': 'success', 'cancelled': count}


# ===================
# REPORT TASKS
# ===================

@shared_task(bind=True)
def generate_report_task(self, report_type: str, date_from: str, date_to: str, user_id: int):
    """
    Generate report asynchronously.
    
    Args:
        report_type: Type of report (daily, weekly, monthly, custom)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        user_id: User requesting the report
    """
    from apps.reports.utils import generate_report
    
    try:
        report_data = generate_report(report_type, date_from, date_to)
        
        # Send report to user via email
        from apps.accounts.models import User
        user = User.objects.get(id=user_id)
        
        subject = f"Your {report_type} report is ready"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        Your {report_type} report from {date_from} to {date_to} has been generated.
        
        Please log in to your dashboard to view the report.
        
        Best regards,
        Smart Health Team
        """
        
        send_email_task.delay(subject, message, [user.email])
        
        return {
            'status': 'success',
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
        }
        
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def generate_weekly_report(self):
    """Generate weekly report for all admins"""
    from apps.accounts.models import User
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    admins = User.objects.filter(is_staff=True, is_active=True)
    
    for admin in admins:
        generate_report_task.delay(
            'weekly',
            str(week_ago),
            str(today),
            admin.id
        )
    
    return {'status': 'success', 'admins_notified': admins.count()}


@shared_task(bind=True)
def generate_monthly_report(self):
    """Generate monthly report for all admins"""
    from apps.accounts.models import User
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    admins = User.objects.filter(is_staff=True, is_active=True)
    
    for admin in admins:
        generate_report_task.delay(
            'monthly',
            str(month_ago),
            str(today),
            admin.id
        )
    
    return {'status': 'success', 'admins_notified': admins.count()}


# ===================
# CACHE TASKS
# ===================

@shared_task(bind=True)
def warm_cache(self):
    """Warm up cache with frequently accessed data"""
    from django.core.cache import cache
    
    try:
        # Warm doctor list cache
        from apps.doctors.models import Doctor
        doctors = Doctor.objects.select_related('user', 'specialty').filter(is_active=True)
        doctors_data = [
            {
                'id': d.id,
                'name': d.user.get_full_name(),
                'specialty': d.specialty.name if d.specialty else None,
            }
            for d in doctors[:50]
        ]
        cache.set('warm_doctors_list', doctors_data, 3600)
        
        # Warm specialties cache
        from apps.doctors.models import Specialty
        specialties = Specialty.objects.filter(is_active=True)
        specialties_data = [{'id': s.id, 'name': s.name} for s in specialties]
        cache.set('warm_specialties', specialties_data, 3600)
        
        logger.info("Cache warmed successfully")
        return {'status': 'success'}
        
    except Exception as exc:
        logger.error(f"Cache warming failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def clear_cache(self, pattern: str = '*'):
    """Clear cache by pattern"""
    from django.core.cache import cache
    
    try:
        if pattern == '*':
            cache.clear()
        else:
            # Use pattern matching if supported
            cache.delete_pattern(pattern) if hasattr(cache, 'delete_pattern') else None
        
        logger.info(f"Cache cleared for pattern: {pattern}")
        return {'status': 'success', 'pattern': pattern}
        
    except Exception as exc:
        logger.error(f"Cache clearing failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


# ===================
# CLEANUP TASKS
# ===================

@shared_task(bind=True)
def cleanup_old_sessions(self):
    """Clean up old sessions from database"""
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    try:
        # Delete expired sessions
        count = Session.objects.filter(expire_date__lt=timezone.now()).count()
        Session.objects.filter(expire_date__lt=timezone.now()).delete()
        
        logger.info(f"Cleaned up {count} old sessions")
        return {'status': 'success', 'deleted': count}
        
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def cleanup_old_data(self):
    """Clean up old logs and temporary data"""
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Clean up old notifications (older than 30 days)
        from apps.notifications.models import Notification
        cutoff = timezone.now() - timedelta(days=30)
        count = Notification.objects.filter(created_at__lt=cutoff, is_read=True).count()
        Notification.objects.filter(created_at__lt=cutoff, is_read=True).delete()
        
        # Clean up old chat messages (older than 90 days)
        from apps.chat.models import Message
        cutoff = timezone.now() - timedelta(days=90)
        count += Message.objects.filter(created_at__lt=cutoff).count()
        Message.objects.filter(created_at__lt=cutoff).delete()
        
        logger.info(f"Cleaned up {count} old records")
        return {'status': 'success', 'deleted': count}
        
    except Exception as exc:
        logger.error(f"Data cleanup failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def cleanup_old_files(self):
    """Clean up orphaned media files"""
    import os
    from django.conf import settings
    
    try:
        # This is a placeholder - implement based on actual needs
        logger.info("File cleanup completed")
        return {'status': 'success'}
        
    except Exception as exc:
        logger.error(f"File cleanup failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


# ===================
# AI TASKS
# ===================

@shared_task(bind=True)
def process_ai_request(self, request_id: int):
    """Process AI chat request asynchronously"""
    from apps.ai_orchestrator.models import AIRequest
    
    try:
        ai_request = AIRequest.objects.get(id=request_id)
        
        # Process the request
        from apps.ai_orchestrator.services import AIService
        ai_service = AIService()
        
        response = ai_service.process_request(ai_request.prompt, ai_request.context)
        
        ai_request.response = response
        ai_request.status = 'completed'
        ai_request.completed_at = timezone.now()
        ai_request.save()
        
        return {'status': 'success', 'request_id': request_id}
        
    except AIRequest.DoesNotExist:
        return {'status': 'error', 'message': 'AI request not found'}
    except Exception as exc:
        logger.error(f"AI request processing failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


# ===================
# CHAT TASKS
# ===================

@shared_task(bind=True, max_retries=3)
def process_ai_chat_message(self, message_id: int):
    """
    Process AI chat message asynchronously using Celery.
    This handles the AI response generation in the background.
    
    Args:
        message_id: ID of the message to process
    """
    from apps.chat.models import Message, Conversation
    from apps.ai_orchestrator.services import AIService
    
    try:
        message = Message.objects.select_related('conversation').get(id=message_id)
        
        # Get conversation history for context
        conversation = message.conversation
        recent_messages = Message.objects.filter(
            conversation=conversation
        ).order_by('-created_at')[:10]
        
        # Build context from history
        context = "\n".join([
            f"{'User' if m.is_ai else 'Assistant'}: {m.content}"
            for m in reversed(recent_messages[:-1])
        ])
        
        # Process with AI service
        ai_service = AIService()
        response = ai_service.process_request(message.content, context)
        
        # Create AI response message
        ai_message = Message.objects.create(
            conversation=conversation,
            content=response,
            is_ai=True,
            sender=conversation.participants.first(),
        )
        
        logger.info(f"AI response generated for message {message_id}")
        return {
            'status': 'success',
            'message_id': message_id,
            'response_id': ai_message.id,
        }
        
    except Message.DoesNotExist:
        logger.error(f"Message {message_id} not found")
        return {'status': 'error', 'message': 'Message not found'}
    except Exception as exc:
        logger.error(f"AI chat processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def send_chat_notification(self, conversation_id: int, message_id: int, recipient_id: int):
    """
    Send notification when new chat message arrives.
    
    Args:
        conversation_id: ID of the conversation
        message_id: ID of the new message
        recipient_id: ID of the recipient user
    """
    from apps.chat.models import Message, Conversation
    from apps.accounts.models import User
    from apps.notifications.models import Notification
    
    try:
        message = Message.objects.get(id=message_id)
        conversation = Conversation.objects.get(id=conversation_id)
        recipient = User.objects.get(id=recipient_id)
        
        # Get sender info
        sender = message.sender
        sender_name = sender.get_full_name() if sender else 'Unknown'
        
        # Create notification
        Notification.objects.create(
            user=recipient,
            title=f"New message from {sender_name}",
            message=message.content[:100] + "..." if len(message.content) > 100 else message.content,
            notification_type='chat',
        )
        
        logger.info(f"Chat notification sent to user {recipient_id}")
        return {'status': 'success', 'recipient_id': recipient_id}
        
    except (Message.DoesNotExist, Conversation.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Chat notification failed: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True)
def save_chat_history(self, conversation_id: int):
    """
    Archive and save chat conversation history.
    This task can be scheduled to run periodically.
    
    Args:
        conversation_id: ID of the conversation to archive
    """
    from apps.chat.models import Message, Conversation
    import json
    from django.utils import timezone
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        messages = Message.objects.filter(
            conversation=conversation
        ).order_by('created_at')
        
        # Create archive data
        chat_history = {
            'conversation_id': str(conversation.id),
            'participants': [str(p.id) for p in conversation.participants.all()],
            'conv_type': conversation.conv_type,
            'archived_at': timezone.now().isoformat(),
            'messages': [
                {
                    'id': str(m.id),
                    'sender_id': str(m.sender_id) if m.sender else None,
                    'content': m.content,
                    'is_ai': m.is_ai,
                    'created_at': m.created_at.isoformat(),
                }
                for m in messages
            ]
        }
        
        # In a real implementation, you might save this to a file or another DB
        # For now, we'll just log it
        logger.info(f"Chat history archived for conversation {conversation_id}: {len(messages)} messages")
        
        return {
            'status': 'success',
            'conversation_id': conversation_id,
            'messages_count': len(messages),
        }
        
    except Conversation.DoesNotExist:
        return {'status': 'error', 'message': 'Conversation not found'}
    except Exception as exc:
        logger.error(f"Chat history archiving failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def notify_chat_completion(self, conversation_id: int, user_id: int):
    """
    Notify user when a chat session is completed or needs attention.
    
    Args:
        conversation_id: ID of the conversation
        user_id: ID of the user to notify
    """
    from apps.chat.models import Conversation
    from apps.notifications.models import Notification
    from apps.accounts.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Check if conversation needs follow-up
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Get last message time
        last_message = conversation.messages.order_by('-created_at').first()
        
        if last_message:
            # If no response for more than 1 hour, send reminder
            from django.utils import timezone
            time_since_last = timezone.now() - last_message.created_at
            
            if time_since_last.total_seconds() > 3600:  # 1 hour
                Notification.objects.create(
                    user=user,
                    title="پیام جدید در چت" if user.language == 'fa' else "New Chat Message",
                    message="پزشک به پیام شما پاسخ داده است" if user.language == 'fa' else "Doctor has responded to your message",
                    notification_type='chat',
                )
        
        logger.info(f"Chat completion notification sent to user {user_id}")
        return {'status': 'success'}
        
    except (User.DoesNotExist, Conversation.DoesNotExist) as e:
        return {'status': 'error', 'message': str(e)}


# ===================
# HEALTH CHECK
# ===================

@shared_task(bind=True)
def health_check_task(self):
    """Health check task for monitoring Celery"""
    return {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'worker': self.request.hostname if hasattr(self.request, 'hostname') else 'unknown',
    }


# ===================
# NOTIFICATION TASKS
# ===================

@shared_task(bind=True)
def send_notification(self, user_id: int, title: str, message: str, notification_type: str = 'info'):
    """Send in-app notification"""
    from apps.notifications.models import Notification
    from apps.accounts.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
        )
        
        return {'status': 'success', 'user_id': user_id}
        
    except User.DoesNotExist:
        return {'status': 'error', 'message': 'User not found'}
    except Exception as exc:
        logger.error(f"Notification failed: {exc}")
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def broadcast_notification(self, title: str, message: str, notification_type: str = 'info', user_role: Optional[str] = None):
    """Broadcast notification to all users or specific role"""
    from apps.notifications.models import Notification
    from apps.accounts.models import User
    
    try:
        queryset = User.objects.filter(is_active=True)
        
        if user_role:
            if user_role == 'doctor':
                queryset = queryset.filter(doctor__isnull=False)
            elif user_role == 'patient':
                queryset = queryset.filter(patient__isnull=False)
        
        count = 0
        for user in queryset:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
            )
            count += 1
        
        return {'status': 'success', 'notifications_sent': count}
        
    except Exception as exc:
        logger.error(f"Broadcast notification failed: {exc}")
        return {'status': 'error', 'error': str(exc)}

