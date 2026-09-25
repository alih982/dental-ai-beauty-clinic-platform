from rest_framework import serializers
from apps.chat.models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'is_ai', 'timestamp', 'is_read']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'conv_type', 'participants', 'other_participant', 'messages', 'created_at', 'updated_at']

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        participant = obj.participants.exclude(id=request.user.id).first()
        if participant:
            full_name = participant.get_full_name()
            
            # Try to get doctor info from appointment
            doctor_info = None
            try:
                from apps.appointments.domain.models import Appointment
                # Find appointment that has this conversation
                appointment = Appointment.objects.filter(
                    conversation_id=obj.id,
                    doctor__user=participant
                ).first()
                
                if appointment:
                    doctor_info = {
                        'specialty': appointment.doctor.specialty if hasattr(appointment.doctor, 'specialty') else None,
                        'appointment_date': appointment.appointment_date.isoformat() if appointment.appointment_date else None,
                        'appointment_time': str(appointment.appointment_time) if appointment.appointment_time else None,
                        'appointment_number': appointment.appointment_number,
                    }
            except Exception:
                pass
            
            result = {
                'id': participant.id,
                'username': participant.username,
                'full_name': full_name if full_name else participant.username
            }
            
            # Add doctor info if available
            if doctor_info:
                result['doctor_info'] = doctor_info
                
            return result
        return None
