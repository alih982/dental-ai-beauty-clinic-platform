from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.chat.models import Conversation, Message
from apps.chat.serializers import ConversationSerializer, MessageSerializer
from apps.chat.domain.services import ChatService
import json

class ChatStreamView(APIView):
    """
    API View for Streaming AI Responses.
    """
    serializer_class = ConversationSerializer
    permission_classes = [AllowAny] # For demo purposes, allow guests. In prod should be IsAuthenticated.
    
    def post(self, request):
        message = request.data.get('message')
        if not message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        service = ChatService()
        
        def event_stream():
            try:
                for chunk in service.stream_reply(message):
                    # SSE Format: data: <content>\n\n
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )

class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for fetching conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='create')
    def create_conversation(self, request):
        """
        Create or get a conversation with a doctor.
        """
        from django.contrib.auth import get_user_model
        from apps.doctors.models import Doctor
        
        User = get_user_model()
        doctor_id = request.data.get('doctor_id')
        
        if not doctor_id:
            return Response(
                {'error': 'doctor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            doctor_user = doctor.user
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if conversation already exists
        existing_conv = Conversation.objects.filter(
            conv_type='patient_doctor',
            participants=request.user
        ).filter(
            participants=doctor_user
        ).first()
        
        if existing_conv:
            serializer = self.get_serializer(existing_conv)
            return Response(serializer.data)
        
        # Create new conversation
        conversation = Conversation.objects.create(conv_type='patient_doctor')
        conversation.participants.add(request.user)
        conversation.participants.add(doctor_user)
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='appointment-doctors')
    def get_appointment_doctors(self, request):
        """
        Get doctors from confirmed/pending appointments for the current user.
        This is used to show doctors in chat when no conversation exists yet.
        """
        from apps.appointments.domain.models import Appointment
        from apps.doctors.models import Doctor
        
        user = request.user
        
        # Get appointments for this user (as patient)
        # First check if user has a patient profile
        patient = None
        if hasattr(user, 'patient_profile'):
            patient = user.patient_profile
        
        # Get appointments where user is the patient
        if patient:
            appointments = Appointment.objects.filter(
                patient=patient,
                status__in=['pending', 'confirmed']
            ).select_related('doctor', 'doctor__user').order_by('-appointment_date', '-appointment_time')
        else:
            # For guest bookings, try to match by phone number
            appointments = Appointment.objects.filter(
                patient_phone=user.phone_number,
                status__in=['pending', 'confirmed']
            ).select_related('doctor', 'doctor__user').order_by('-appointment_date', '-appointment_time')
        
        # Get unique doctors from appointments
        doctors_data = []
        seen_doctor_ids = set()
        
        for apt in appointments:
            doctor = apt.doctor
            if doctor.id not in seen_doctor_ids:
                seen_doctor_ids.add(doctor.id)
                doctor_user = doctor.user
                doctors_data.append({
                    'id': str(doctor.id),
                    'doctor_id': doctor.id,
                    'user_id': doctor_user.id if doctor_user else None,
                    'full_name': doctor.get_full_name(),
                    'specialty': doctor.specialty,
                    'appointment_date': apt.appointment_date.isoformat(),
                    'appointment_time': apt.appointment_time.isoformat(),
                    'appointment_id': str(apt.id),
                    'conversation_id': str(apt.conversation.id) if apt.conversation else None,
                    'status': apt.status,
                })
        
        return Response({
            'success': True,
            'count': len(doctors_data),
            'data': doctors_data
        })

class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for fetching messages within a conversation.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            return Message.objects.filter(
                conversation_id=conversation_id,
                conversation__participants=self.request.user
            )
        return Message.objects.none()
