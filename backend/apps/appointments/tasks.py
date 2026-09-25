"""
Celery Tasks for Appointments App

This module contains all Celery tasks for appointment management,
including chat session management and prescription notifications.

All tasks use the centralized Celery configuration from config.celery_config.

DYNAMIC REDIS CONFIGURATION:
    All Redis settings are loaded from config.dynamic_settings.
    To change Redis configuration, simply update these environment variables:
    - REDIS_URL: Base Redis URL (default: redis://maggicaihub.com:6379)
    - REDIS_DB_CELERY: Celery broker/backend DB (default: 0)
    - REDIS_DB_CHANNELS: WebSocket channels DB (default: 1)
    - REDIS_DB_CACHE: Cache DB (default: 2)
    - REDIS_DB_SESSIONS: Session DB (default: 3)
    
    Example: Change REDIS_DB_CELERY=5 to use Redis DB 5 for Celery.
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


def activate_chat_session_sync(appointment_id: int):
    """
    Synchronous function to activate chat session.
    Can be called directly without Celery for immediate activation.
    
    Returns dict with status and details.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from apps.appointments.domain.models import Appointment
        from apps.chat.models import Conversation
        
        logger.info(f"🔔 Activating chat session for appointment {appointment_id}")
        
        appointment = Appointment.objects.get(id=appointment_id)
        logger.info(f"📋 Appointment found: {appointment.appointment_number}, status: {appointment.status}, payment: {appointment.payment_status}")
        
        # Check if appointment is eligible for chat
        if appointment.payment_status != 'paid':
            logger.warning(f"Appointment {appointment_id} is not paid yet")
            return {'status': 'skipped', 'reason': 'not_paid'}
        
        # Use Enum comparison
        valid_statuses = [Appointment.Status.CONFIRMED, Appointment.Status.PENDING]
        if appointment.status not in valid_statuses:
            logger.warning(f"Appointment {appointment_id} status is {appointment.status}")
            return {'status': 'skipped', 'reason': 'invalid_status'}
        
        # Get doctor and patient users
        doctor_user = appointment.doctor.user
        patient_user = appointment.patient.user if appointment.patient else None
        
        if not patient_user:
            # Try to get or create a user based on the patient's phone
            from django.contrib.auth import get_user_model
            User = get_user_model()
            phone = appointment.patient_phone
            
            # Find user by phone number
            patient_user = User.objects.filter(phone_number=phone).first()
            if not patient_user:
                # Create a bare minimum user so they have access when they sign in later
                patient_user = User.objects.create_user(
                    username=phone,
                    phone_number=phone,
                    password=User.objects.make_random_password()
                )
                
            # Make sure we have a patient profile attached
            if not appointment.patient:
                from apps.patients.models import Patient
                patient, _ = Patient.objects.get_or_create(
                    phone=phone,
                    defaults={'user': patient_user}
                )
                appointment.patient = patient
                appointment.save()
        
        # Check if conversation already exists
        existing_conv = Conversation.objects.filter(
            conv_type='patient_doctor',
            participants=doctor_user
        ).filter(
            participants=patient_user
        ).first()
        
        if existing_conv:
            conversation = existing_conv
        else:
            conversation = Conversation.objects.create(conv_type='patient_doctor')
            conversation.participants.add(doctor_user, patient_user)
        
        # Update appointment with conversation ID
        appointment.conversation_id = conversation.id
        appointment.save()
        
        # Send notification to both parties via WebSocket
        channel_layer = get_channel_layer()
        
        # Notify patient
        async_to_sync(channel_layer.group_send)(
            f"user_{patient_user.id}",
            {
                "type": "chat_message",
                "content": f"Your appointment with Dr. {doctor_user.get_full_name()} is ready. You can now start chatting.",
                "metadata": {
                    "type": "SESSION_ACTIVATED",
                    "appointment_id": str(appointment.id),
                    "conversation_id": str(conversation.id),
                    "doctor_name": doctor_user.get_full_name(),
                },
                "sender_id": "SYSTEM",
                "sender_name": "System"
            }
        )
        
        # Notify doctor
        async_to_sync(channel_layer.group_send)(
            f"user_{doctor_user.id}",
            {
                "type": "chat_message",
                "content": f"Patient {appointment.patient_name} is waiting for consultation.",
                "metadata": {
                    "type": "SESSION_ACTIVATED",
                    "appointment_id": str(appointment.id),
                    "conversation_id": str(conversation.id),
                    "patient_name": appointment.patient_name,
                },
                "sender_id": "SYSTEM",
                "sender_name": "System"
            }
        )
        
        logger.info(f"Chat session activated synchronously for appointment {appointment_id}")
        return {
            'status': 'success',
            'conversation_id': str(conversation.id),
            'appointment_id': str(appointment.id)
        }
        
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return {'status': 'error', 'reason': 'appointment_not_found'}
    except Exception as e:
        logger.error(f"Error activating chat session: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.on_payment_success')
def on_payment_success(self, appointment_id: int):
    """
    Triggered when payment is successful.
    This is the main entry point for post-payment operations.
    
    Flow:
    1. Update appointment payment_status to 'paid'
    2. Confirm the appointment
    3. Activate chat session (synchronous for immediate result)
    4. Notify patient and doctor
    """
    try:
        from apps.appointments.domain.models import Appointment
        
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Step 1: Update payment status
        appointment.payment_status = 'paid'
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        
        logger.info(f"Payment confirmed for appointment {appointment_id}")
        
        # Step 2: Activate chat session synchronously for immediate result
        activate_chat_session_sync(appointment_id)
        
        # Step 3: Send notifications (async via Celery)
        notify_appointment_confirmed.delay(appointment_id)
        
        return {
            'status': 'success',
            'appointment_id': str(appointment_id),
            'message': 'Payment processed, chat session activated'
        }
        
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return {'status': 'error', 'reason': 'appointment_not_found'}
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.notify_appointment_confirmed')
def notify_appointment_confirmed(self, appointment_id: int):
    """
    Sends notifications to patient and doctor when appointment is confirmed.
    """
    try:
        from apps.appointments.domain.models import Appointment
        from apps.notifications.tasks import send_live_notification
        
        appointment = Appointment.objects.get(id=appointment_id)
        
        doctor_user = appointment.doctor.user
        patient_user = appointment.patient.user if appointment.patient else None
        
        # Notify patient
        if patient_user:
            send_live_notification.delay(
                user_id=patient_user.id,
                title="Appointment Confirmed ✅",
                message=f"Your appointment with Dr. {doctor_user.get_full_name()} has been confirmed. You can now start chatting!",
                notification_type='success',
                link=f"/consultation/{doctor_user.id}"
            )
        
        # Notify doctor
        send_live_notification.delay(
            user_id=doctor_user.id,
            title="New Patient Booking 🎉",
            message=f"{appointment.patient_name} has booked an appointment. Time: {appointment.appointment_date} at {appointment.appointment_time}",
            notification_type='info',
            link=f"/dashboard/doctor"
        )
        
        return {'status': 'success', 'appointment_id': str(appointment_id)}
        
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.activate_chat_session')
def activate_chat_session(self, appointment_id: int):
    """
    Activates a chat session for a confirmed/paid appointment.
    
    This task is triggered when:
    1. Appointment is confirmed
    2. Payment is completed
    3. Doctor accepts the appointment
    
    It creates a conversation and notifies both patient and doctor.
    """
    try:
        from apps.appointments.domain.models import Appointment
        from apps.chat.models import Conversation
        
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Check if appointment is eligible for chat
        if appointment.payment_status != 'paid':
            logger.warning(f"Appointment {appointment_id} is not paid yet")
            return {'status': 'skipped', 'reason': 'not_paid'}
        
        # Fix: Use Enum comparison instead of string comparison
        from apps.appointments.domain.models import Appointment
        valid_statuses = [Appointment.Status.CONFIRMED, Appointment.Status.PENDING]
        if appointment.status not in valid_statuses:
            logger.warning(f"Appointment {appointment_id} status is {appointment.status}")
            return {'status': 'skipped', 'reason': 'invalid_status'}
        
        # Create or get conversation
        doctor_user = appointment.doctor.user
        patient_user = appointment.patient.user if appointment.patient else None
        
        if not patient_user:
            # Let's try to get or create a user based on the patient's phone
            from django.contrib.auth import get_user_model
            User = get_user_model()
            phone = appointment.patient_phone
            
            # Find user by phone number
            patient_user = User.objects.filter(phone_number=phone).first()
            if not patient_user:
                # Create a bare minimum user so they have access when they sign in later
                patient_user = User.objects.create_user(
                    username=phone,
                    phone_number=phone,
                    password=User.objects.make_random_password()
                )
                
            # Make sure we have a patient profile attached
            if not appointment.patient:
                from apps.patients.models import Patient
                patient, _ = Patient.objects.get_or_create(
                    phone=phone,
                    defaults={'user': patient_user}
                )
                appointment.patient = patient
                appointment.save()
        
        # Check if conversation already exists
        existing_conv = Conversation.objects.filter(
            conv_type='patient_doctor',
            participants=doctor_user
        ).filter(
            participants=patient_user
        ).first()
        
        if existing_conv:
            conversation = existing_conv
        else:
            conversation = Conversation.objects.create(conv_type='patient_doctor')
            conversation.participants.add(doctor_user, patient_user)
        
        # Update appointment with conversation ID
        appointment.conversation_id = conversation.id
        appointment.save()
        
        # Send notification to both parties via WebSocket
        channel_layer = get_channel_layer()
        
        # Notify patient
        async_to_sync(channel_layer.group_send)(
            f"user_{patient_user.id}",
            {
                "type": "chat_message",
                "content": f"Your appointment with Dr. {doctor_user.get_full_name()} is ready. You can now start chatting.",
                "metadata": {
                    "type": "SESSION_ACTIVATED",
                    "appointment_id": str(appointment.id),
                    "conversation_id": str(conversation.id),
                    "doctor_name": doctor_user.get_full_name(),
                },
                "sender_id": "SYSTEM",
                "sender_name": "System"
            }
        )
        
        # Notify doctor
        async_to_sync(channel_layer.group_send)(
            f"user_{doctor_user.id}",
            {
                "type": "chat_message",
                "content": f"Patient {appointment.patient_name} is waiting for consultation.",
                "metadata": {
                    "type": "SESSION_ACTIVATED",
                    "appointment_id": str(appointment.id),
                    "conversation_id": str(conversation.id),
                    "patient_name": appointment.patient_name,
                },
                "sender_id": "SYSTEM",
                "sender_name": "System"
            }
        )
        
        # Also send live notifications via Celery for better reliability
        from apps.notifications.tasks import send_live_notification
        
        send_live_notification.delay(
            user_id=patient_user.id,
            title="Chat Session Activated 💬",
            message=f"Your consultation with Dr. {doctor_user.get_full_name()} is ready!",
            notification_type='success',
            link=f"/consultation/{doctor_user.id}"
        )
        
        send_live_notification.delay(
            user_id=doctor_user.id,
            title="New Patient Ready 👨‍⚕️",
            message=f"{appointment.patient_name} is waiting for you in the chat.",
            notification_type='info',
            link=f"/consultation/{patient_user.id}"
        )
        
        logger.info(f"Chat session activated for appointment {appointment_id}")
        return {
            'status': 'success',
            'conversation_id': str(conversation.id),
            'appointment_id': str(appointment.id)
        }
        
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return {'status': 'error', 'reason': 'appointment_not_found'}
    except Exception as e:
        logger.error(f"Error activating chat session: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.end_chat_session')
def end_chat_session(self, appointment_id: int):
    """
    Ends a chat session for an appointment.
    
    This task is triggered when:
    1. Doctor finishes the session
    2. Appointment is cancelled
    3. Appointment time expires
    """
    try:
        from apps.appointments.domain.models import Appointment
        
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Update appointment status
        appointment.status = 'completed'
        appointment.save()
        
        # Send session end notification
        if appointment.patient and appointment.patient.user:
            channel_layer = get_channel_layer()
            
            async_to_sync(channel_layer.group_send)(
                f"user_{appointment.patient.user.id}",
                {
                    "type": "chat_message",
                    "content": f"Your consultation session with Dr. {appointment.doctor.user.get_full_name()} has ended.",
                    "metadata": {
                        "type": "SESSION_ENDED",
                        "appointment_id": str(appointment.id),
                        "checkout_url": "/payment/checkout",
                    },
                    "sender_id": "SYSTEM",
                    "sender_name": "System"
                }
            )
        
        logger.info(f"Chat session ended for appointment {appointment_id}")
        return {'status': 'success', 'appointment_id': str(appointment_id)}
        
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return {'status': 'error', 'reason': 'appointment_not_found'}
    except Exception as e:
        logger.error(f"Error ending chat session: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.send_appointment_reminder')
def send_appointment_reminder(self, appointment_id: int):
    """
    Sends a reminder notification before appointment time.
    """
    try:
        from apps.appointments.domain.models import Appointment
        from apps.notifications.tasks import send_live_notification
        
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Calculate time until appointment
        from django.utils import timezone
        now = timezone.now()
        
        # Combine date and time for comparison
        from datetime import datetime, timedelta
        appointment_datetime = datetime.combine(
            appointment.appointment_date,
            appointment.appointment_time
        )
        
        # Make timezone aware
        if timezone.is_naive(appointment_datetime):
            appointment_datetime = timezone.make_aware(appointment_datetime)
        
        time_diff = appointment_datetime - now
        
        # Determine reminder message based on time
        if time_diff > timedelta(hours=24):
            message = f"Your appointment is tomorrow at {appointment.appointment_time}"
            reminder_type = 'reminder_tomorrow'
        elif time_diff > timedelta(hours=1):
            message = f"Your appointment is in {time_diff.seconds // 3600} hours"
            reminder_type = 'reminder_hours'
        else:
            message = f"Your appointment starts in {time_diff.seconds // 60} minutes"
            reminder_type = 'reminder_minutes'
        
        # Send to patient
        if appointment.patient and appointment.patient.user:
            send_live_notification.delay(
                user_id=appointment.patient.user.id,
                title="Appointment Reminder",
                message=message,
                notification_type=reminder_type,
                link=f"/consultation/{appointment.doctor.user.id}"
            )
        
        # Mark reminder as sent
        appointment.reminder_sent = True
        appointment.save()
        
        return {'status': 'success', 'appointment_id': str(appointment_id)}
        
    except Appointment.DoesNotExist:
        return {'status': 'error', 'reason': 'appointment_not_found'}
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.cleanup_expired_sessions')
def cleanup_expired_sessions(self):
    """
    Periodic task to clean up expired chat sessions.
    
    This runs periodically to:
    1. End sessions that have exceeded their time limit
    2. Mark no-show appointments
    3. Clean up old conversation data
    """
    try:
        from apps.appointments.domain.models import Appointment
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        # Find appointments that should have ended
        expired_appointments = Appointment.objects.filter(
            status__in=['confirmed', 'pending'],
            appointment_date__lt=now.date()
        )
        
        ended_count = 0
        for appointment in expired_appointments:
            # If appointment time has passed by more than 1 hour
            appointment_datetime = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time
            )
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            
            if now - appointment_datetime > timedelta(hours=1):
                appointment.status = 'no_show'
                appointment.save()
                ended_count += 1
        
        logger.info(f"Cleaned up {ended_count} expired sessions")
        return {'status': 'success', 'ended_count': ended_count}
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.sync_appointments')
def sync_appointments(self):
    """
    Periodic task to sync appointment data and trigger chat sessions.
    """
    try:
        from apps.appointments.domain.models import Appointment
        
        # Find paid appointments that haven't activated chat yet
        # Use Enum values for status comparison
        pending_activations = Appointment.objects.filter(
            payment_status='paid',
            status__in=['confirmed', 'pending'],
            conversation_id__isnull=True
        )
        
        activated_count = 0
        for appointment in pending_activations:
            # Use synchronous function for immediate activation
            activate_chat_session_sync(appointment.id)
            activated_count += 1
        
        logger.info(f"Synced {activated_count} appointments")
        return {'status': 'success', 'activated_count': activated_count}
        
    except Exception as e:
        logger.error(f"Error syncing appointments: {str(e)}")
        return {'status': 'error', 'reason': str(e)}


@shared_task(bind=True, name='apps.appointments.tasks.check_appointment_status')
def check_appointment_status(self, appointment_id: int):
    """
    Checks and updates appointment status based on payment and time.
    """
    try:
        from apps.appointments.domain.models import Appointment
        
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Check if appointment should be cancelled (not paid within 24 hours)
        if appointment.payment_status == 'pending':
            created_at = appointment.created_at
            if timezone.now() - created_at > timedelta(hours=24):
                appointment.status = 'cancelled'
                appointment.save()
                return {'status': 'cancelled', 'reason': 'payment_timeout'}
        
        return {'status': 'ok', 'appointment_id': str(appointment_id)}
        
    except Appointment.DoesNotExist:
        return {'status': 'error', 'reason': 'appointment_not_found'}
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}

