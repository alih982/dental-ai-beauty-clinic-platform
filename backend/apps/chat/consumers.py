import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

try:
    from apps.core.models import SystemSettings, ChatMode as SystemChatMode
    SYSTEM_SETTINGS_AVAILABLE = True
except ImportError:
    class SystemChatMode:
        RAG = 'rag'
        FINE_TUNED = 'fine_tuned'
        HUMAN_SUPPORT = 'human_support'
    SYSTEM_SETTINGS_AVAILABLE = False


# ... rest of the imports ...

from apps.chat.models import Conversation, Message
from apps.ai_orchestrator.services import AIService
from apps.appointments.domain.models import Appointment
from apps.notifications.tasks import send_live_notification
from apps.appointments.tasks import activate_chat_session, end_chat_session
from django.db.models import Q

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope.get("user")
            self.is_anonymous = not self.user or not hasattr(self.user, 'is_authenticated') or not self.user.is_authenticated
            
            if not self.is_anonymous:
                self.room_group_name = f"user_{self.user.id}"
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info(f"User {self.user.id} connected to chat")
            else:
                logger.info(f"Guest connected to chat (AI chat only)")
                self.room_group_name = None

            await self.accept()
        except Exception as e:
            logger.error(f"WebSocket connect error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and self.room_group_name and not self.is_anonymous:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'content': 'Invalid JSON format'
            }))
            return
            
        message_type = data.get('type')
        content = data.get('message', data.get('content', ''))
        
        # Get system chat mode
        chat_mode = await self.get_chat_mode()
        
        # Route based on system chat mode
        if message_type == 'ai_chat':
            if chat_mode == SystemChatMode.HUMAN_SUPPORT:
                # Human support mode - create ticket/notification
                await self.handle_human_support(content)
            elif chat_mode == SystemChatMode.RAG:
                # RAG system mode (Information specialized)
                await self.handle_ai_chat(content, enable_rag=True, force_company_info=True)
            elif chat_mode == SystemChatMode.FINE_TUNED:
                # Fine-tuned AI mode
                await self.handle_ai_chat(content, enable_rag=False, force_company_info=False)
            else:
                # Default fallback
                await self.handle_ai_chat(content, enable_rag=data.get('enable_rag', False), force_company_info=False)
            
        elif message_type == 'private_message':
            if self.is_anonymous:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': 'Authentication required for private messaging'
                }))
                return
                
            recipient_id = data.get('recipient_id')
            if recipient_id:
                # Check if user has access to chat with this doctor
                # Allow if there's a confirmed/pending appointment OR if conversation already exists
                has_access = await self.has_paid_appointment(recipient_id)
                has_conversation = await self.has_existing_conversation(recipient_id)
                
                if not has_access and not has_conversation:
                    # Try to create conversation from appointment
                    created = await self.try_create_conversation_from_appointment(recipient_id)
                    if not created:
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'content': 'You must have a paid and confirmed appointment to chat with this doctor.'
                        }))
                        return

                # Get or create conversation
                conv = await self.get_or_create_private_conversation(recipient_id)
                msg = await self.save_message(conv, self.user, content, is_ai=False)

                # Send to recipient via WebSocket group
                await self.channel_layer.group_send(
                    f"user_{recipient_id}",
                    {
                        'type': 'chat_message',
                        'content': content,
                        'message_id': msg.id,
                        'sender_id': self.user.id,
                        'sender_name': self.user.get_full_name() if hasattr(self.user, 'get_full_name') else str(self.user)
                    }
                )

                # Also send back to self to show the message
                await self.send(text_data=json.dumps({
                    'type': 'chat_message',
                    'content': content,
                    'message_id': msg.id,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() if hasattr(self.user, 'get_full_name') else str(self.user),
                    'is_self': True
                }))

        elif message_type == 'clinical_analysis':
            if self.is_anonymous:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': 'Authentication required for clinical analysis'
                }))
                return
                
            conv_id = data.get('conversation_id')
            history = await self.get_conversation_history(conv_id)
            analysis = await AIService.analyze_clinical_context(history)
            
            await self.send(text_data=json.dumps({
                'type': 'ai_decision',
                'analysis': analysis
            }))

        elif message_type == 'send_prescription':
            if self.is_anonymous or not hasattr(self.user, 'doctor_profile'):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': 'Only doctors can send prescriptions'
                }))
                return
                
            recipient_id = data.get('patient_id')
            medications = data.get('medications')
            diagnosis = data.get('diagnosis')
            
            if not recipient_id or not medications or not diagnosis:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': 'Missing prescription data'
                }))
                return
            
            try:
                prescription = await self.create_prescription_async(recipient_id, medications, diagnosis)
                
                conv = await self.get_or_create_private_conversation(recipient_id)
                await self.save_message(conv, self.user, "Issued a new electronic prescription.", metadata={
                    'type': 'PRESCRIPTION',
                    'prescription_id': str(prescription.id),
                    'pdf_url': prescription.pdf_file.url if prescription.pdf_file else None
                })

                await self.channel_layer.group_send(
                    f"user_{recipient_id}",
                    {
                        'type': 'chat_message',
                        'content': "New Prescription Received",
                        'metadata': {
                            'type': 'PRESCRIPTION',
                            'prescription_id': str(prescription.id),
                            'pdf_url': prescription.pdf_file.url if prescription.pdf_file else None
                        },
                        'sender_id': self.user.id,
                        'sender_name': self.user.get_full_name() if hasattr(self.user, 'get_full_name') else str(self.user)
                    }
                )

                send_live_notification.delay(
                    user_id=recipient_id,
                    title="New Electronic Prescription",
                    message=f"Dr. {self.user.get_full_name() if hasattr(self.user, 'get_full_name') else 'Doctor'} has issued a new prescription for you.",
                    notification_type='success',
                    link=f"/dashboard/prescriptions"
                )
            except Exception as e:
                logger.error(f"Prescription error: {str(e)}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': f'Failed to create prescription: {str(e)}'
                }))

        elif message_type == 'finish_session':
            if self.is_anonymous or not hasattr(self.user, 'doctor_profile'):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': 'Only doctors can finish sessions'
                }))
                return
                
            recipient_id = data.get('patient_id')
            appointment_id = data.get('appointment_id')
            
            await self.channel_layer.group_send(
                f"user_{recipient_id}",
                {
                    'type': 'chat_message',
                    'content': "The consultation has been completed by your doctor.",
                    'metadata': {
                        'type': 'SESSION_FINISHED',
                        'checkout_url': '/payment/checkout'
                    },
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() if hasattr(self.user, 'get_full_name') else str(self.user)
                }
            )

            send_live_notification.delay(
                user_id=recipient_id,
                title="Consultation Completed",
                message=f"Your session with Dr. {self.user.get_full_name() if hasattr(self.user, 'get_full_name') else 'Doctor'} has ended.",
                notification_type='info',
                link=f"/dashboard/appointments"
            )
            
            if appointment_id:
                end_chat_session.delay(int(appointment_id))
            
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'content': "Session marked as completed. Patient redirected to checkout.",
                'metadata': {'type': 'SESSION_COMPLETED_SUCCESS'},
                'sender_id': 'SYSTEM',
                'sender_name': 'System'
            }))

        elif message_type == 'start_consultation':
            if self.is_anonymous or not hasattr(self.user, 'doctor_profile'):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': 'Only doctors can start consultations'
                }))
                return
                
            appointment_id = data.get('appointment_id')
            if appointment_id:
                activate_chat_session.delay(int(appointment_id))
                
                await self.send(text_data=json.dumps({
                    'type': 'system_message',
                    'content': 'Chat session activation initiated. Please wait...',
                    'sender_id': 'SYSTEM',
                    'sender_name': 'System'
                }))

    async def handle_ai_chat(self, content, enable_rag=False, force_company_info=False):
        """Handle AI chat based on mode"""
        enable_rag = enable_rag or force_company_info
        
        if not self.is_anonymous:
            conv = await self.get_or_create_ai_conversation()
            await self.save_message(conv, self.user, content, is_ai=False)

        full_response = ""
        try:
            async for chunk in AIService.stream_chat(content, self.user if not self.is_anonymous else None, enable_rag=enable_rag):
                try:
                    if chunk.startswith('{') and '"type": "sources"' in chunk:
                        source_data = json.loads(chunk)
                        await self.send(text_data=json.dumps({
                            'type': 'ai_sources',
                            'sources': source_data.get('sources', []),
                            'sender': 'AI'
                        }))
                        continue
                except:
                    pass

                full_response += chunk
                await self.send(text_data=json.dumps({
                    'type': 'ai_response_chunk',
                    'content': chunk,
                    'sender': 'AI'
                }))
            
            if not self.is_anonymous:
                await self.save_message(conv, None, full_response, is_ai=True)
                
            await self.send(text_data=json.dumps({
                'type': 'ai_response_complete',
                'full_content': full_response,
                'sender': 'AI'
            }))
        except Exception as e:
            logger.error(f"AI chat error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'content': f'AI service error: {str(e)}'
            }))

    async def handle_human_support(self, content):
        """Handle human support mode - notify admins/doctors"""
        if self.is_anonymous:
            await self.send(text_data=json.dumps({
                'type': 'system_message',
                'content': 'لطفاً برای ارتباط با پشتیبانی وارد حساب کاربری خود شوید.',
                'sender': 'SYSTEM'
            }))
            return
        
        # Notify all admins about new support request
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            
            for admin in admins:
                send_live_notification.delay(
                    user_id=admin.id,
                    title="درخواست پشتیبانی جدید",
                    message=f"کاربر {self.user.get_full_name() or self.user.phone_number}: {content[:100]}",
                    notification_type='support',
                    link=f"/dashboard/admin"
                )
            
            # Create conversation for support
            conv = await self.get_or_create_support_conversation()
            await self.save_message(conv, self.user, content, is_ai=False, metadata={'type': 'SUPPORT_REQUEST'})
            
            await self.send(text_data=json.dumps({
                'type': 'system_message',
                'content': 'درخواست شما به تیم پشتیبانی ارسال شد. به زودی با شما تماس گرفته می‌شود.',
                'sender': 'SYSTEM'
            }))
        except Exception as e:
            logger.error(f"Human support error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'content': 'خطا در ارسال درخواست پشتیبانی'
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'content': event['content'],
            'metadata': event.get('metadata'),
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name']
        }))

    @database_sync_to_async
    def get_chat_mode(self):
        """Get current system chat mode"""
        if SYSTEM_SETTINGS_AVAILABLE:
            try:
                settings = SystemSettings.get_settings()
                return settings.chat_mode
            except:
                pass
        return SystemChatMode.AI_RESPONSE

    @database_sync_to_async
    def get_conversation_history(self, conv_id, limit=20):
        messages = Message.objects.filter(conversation_id=conv_id).order_by('-timestamp')[:limit]
        return [
            {
                "sender": m.sender.get_full_name() if m.sender and hasattr(m.sender, 'get_full_name') else "User",
                "content": m.content
            } for m in reversed(messages)
        ]

    @database_sync_to_async
    def create_prescription_async(self, patient_id, medications, diagnosis):
        from apps.prescriptions.application.services import ElectronicPrescriptionService
        from apps.doctors.domain.models import Doctor
        from apps.patients.domain.models import Patient
        
        service = ElectronicPrescriptionService()
        doctor = Doctor.objects.get(user=self.user)
        patient = Patient.objects.get(id=patient_id)
        
        return service.create_prescription(
            doctor=doctor,
            patient=patient,
            medications=medications,
            diagnosis=diagnosis
        )

    @database_sync_to_async
    def has_paid_appointment(self, other_user_id):
        from django.db.models import Q
        
        status_filter = Appointment.Status.CONFIRMED
        payment_filter = 'paid'
        
        return Appointment.objects.filter(
            (Q(doctor__user=self.user) & Q(patient__user_id=other_user_id)) |
            (Q(patient__user=self.user) & Q(doctor__user_id=other_user_id)),
            status=status_filter,
            payment_status=payment_filter
        ).exists()

    @database_sync_to_async
    def has_existing_conversation(self, other_user_id):
        """Check if conversation already exists between users"""
        return Conversation.objects.filter(
            conv_type='patient_doctor',
            participants__id=self.user.id
        ).filter(
            participants__id=other_user_id
        ).exists()

    @database_sync_to_async
    def try_create_conversation_from_appointment(self, recipient_id):
        """Try to create conversation from existing appointment"""
        try:
            # Check if there's any appointment (even pending) between users
            appointment = Appointment.objects.filter(
                (Q(doctor__user=self.user) & Q(patient__user_id=recipient_id)) |
                (Q(patient__user=self.user) & Q(doctor__user_id=recipient_id))
            ).first()

            if appointment:
                # Create conversation
                conv = Conversation.objects.create(conv_type='patient_doctor')
                conv.participants.add(self.user)
                try:
                    recipient = User.objects.get(id=recipient_id)
                    conv.participants.add(recipient)
                except User.DoesNotExist:
                    pass
                logger.info(f"Created conversation from appointment for user {self.user.id} and recipient {recipient_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating conversation from appointment: {str(e)}")
            return False

    @database_sync_to_async
    def get_or_create_ai_conversation(self):
        conv = Conversation.objects.filter(
            conv_type='patient_ai',
            participants__id=self.user.id
        ).first()

        if not conv:
            conv = Conversation.objects.create(conv_type='patient_ai')
            conv.participants.add(self.user)
        return conv

    @database_sync_to_async
    def get_or_create_support_conversation(self):
        """Create or get support conversation"""
        conv = Conversation.objects.filter(
            conv_type='patient_support',
            participants__id=self.user.id
        ).first()

        if not conv:
            conv = Conversation.objects.create(conv_type='patient_support')
            conv.participants.add(self.user)
        return conv

    @database_sync_to_async
    def get_or_create_private_conversation(self, recipient_id):
        conv = Conversation.objects.filter(
            conv_type='patient_doctor',
            participants__id=self.user.id
        ).filter(
            participants__id=recipient_id
        ).first()

        if not conv:
            conv = Conversation.objects.create(conv_type='patient_doctor')
            conv.participants.add(self.user)
            try:
                recipient = User.objects.get(id=recipient_id)
                conv.participants.add(recipient)
            except User.DoesNotExist:
                pass
        return conv

    @database_sync_to_async
    def save_message(self, conversation, sender, content, metadata=None, is_ai=False):
        msg = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content,
            metadata=metadata,
            is_ai=is_ai
        )
        
        if sender and not is_ai and not self.is_anonymous:
            try:
                recipient = conversation.participants.exclude(id=sender.id).first()
                if recipient:
                    send_live_notification.delay(
                        user_id=recipient.id,
                        title=f"New message from {sender.get_full_name() if hasattr(sender, 'get_full_name') else 'User'}",
                        message=content[:50] + "..." if len(content) > 50 else content,
                        notification_type='message',
                        link=f"/dashboard/messages"
                    )
            except Exception as e:
                logger.error(f"Error sending notification: {str(e)}")
                
        return msg

    @database_sync_to_async
    def get_or_create_conversation_from_appointment(self, doctor_id, patient_id):
        """
        Get or create a conversation between doctor and patient based on confirmed appointment.
        This fixes the 'zero doctor' issue after booking.
        """
        try:
            # First try to find existing conversation
            conv = Conversation.objects.filter(
                conv_type='patient_doctor'
            ).filter(
                participants__id=patient_id
            ).filter(
                participants__id=doctor_id
            ).first()

            if conv:
                return conv

            # Check if there's a confirmed appointment between them
            appointment = Appointment.objects.filter(
                Q(doctor__user_id=doctor_id, patient__user_id=patient_id) |
                Q(doctor__user_id=patient_id, patient__user_id=doctor_id),
                status__in=[Appointment.Status.CONFIRMED, Appointment.Status.IN_PROGRESS],
                payment_status='paid'
            ).first()

            if not appointment:
                # Create conversation anyway if no appointment exists yet
                # This handles the case where payment is still pending
                logger.info(f"Creating new conversation for doctor {doctor_id} and patient {patient_id}")

            # Create new conversation
            conv = Conversation.objects.create(conv_type='patient_doctor')
            
            # Add participants
            try:
                doctor_user = User.objects.get(id=doctor_id)
                conv.participants.add(doctor_user)
            except User.DoesNotExist:
                logger.warning(f"Doctor user {doctor_id} not found")
            
            try:
                patient_user = User.objects.get(id=patient_id)
                conv.participants.add(patient_user)
            except User.DoesNotExist:
                logger.warning(f"Patient user {patient_id} not found")

            logger.info(f"Created new conversation {conv.id} between doctor {doctor_id} and patient {patient_id}")
            return conv

        except Exception as e:
            logger.error(f"Error getting/creating conversation from appointment: {str(e)}")
            return None
