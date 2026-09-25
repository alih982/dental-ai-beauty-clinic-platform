"""
Backup of original ChatConsumer for reference
This is the original file before modifications
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from apps.chat.models import Conversation, Message
from apps.ai_orchestrator.services import AIService
from apps.appointments.domain.models import Appointment
from apps.notifications.tasks import send_live_notification
from apps.appointments.tasks import activate_chat_session, end_chat_session

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
        
        if message_type == 'ai_chat':
            enable_rag = data.get('enable_rag', False)
            
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
            
        elif message_type == 'private_message':
            if self.is_anonymous:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': 'Authentication required for private messaging'
                }))
                return
                
            recipient_id = data.get('recipient_id')
            if recipient_id:
                has_access = await self.has_paid_appointment(recipient_id)
                if not has_access:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'content': 'You must have a paid and confirmed appointment to chat with this doctor.'
                    }))
                    return

                conv = await self.get_or_create_private_conversation(recipient_id)
                msg = await self.save_message(conv, self.user, content, is_ai=False)

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

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'content': event['content'],
            'metadata': event.get('metadata'),
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name']
        }))

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
