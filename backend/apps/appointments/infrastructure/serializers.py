"""
DRF Serializers for Appointment API
"""
from rest_framework import serializers
from apps.appointments.domain.models import Appointment, TimeSlot


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot"""
    
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 
                 'duration_minutes', 'is_active']
        read_only_fields = ['id']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment"""
    
    doctor_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_cancel = serializers.SerializerMethodField()
    conversation_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_name', 'patient', 'patient_name', 
            'patient_phone', 'appointment_date', 'appointment_time',
            'status', 'status_display', 'fee', 'payment_status',
            'notes', 'symptoms', 'appointment_number', 'can_cancel',
            'conversation', 'conversation_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'appointment_number', 'created_at', 'updated_at']
    
    def get_doctor_name(self, obj):
        """Get doctor full name"""
        return obj.doctor.get_full_name() if obj.doctor else ''
    
    def get_can_cancel(self, obj):
        """Check if appointment can be cancelled"""
        return obj.can_cancel()
    
    def get_conversation_id(self, obj):
        """Get conversation ID if exists"""
        return obj.conversation.id if obj.conversation else None


class BookAppointmentSerializer(serializers.Serializer):
    """Serializer for booking appointment request"""
    
    doctor_id = serializers.UUIDField(required=True)
    appointment_date = serializers.DateField(required=True)
    appointment_time = serializers.TimeField(required=True)
    patient_name = serializers.CharField(max_length=255, required=True)
    patient_phone = serializers.CharField(max_length=15, required=True)
    symptoms = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_patient_phone(self, value):
        """Validate phone number format"""
        from apps.core.validators import PhoneNumberValidator
        return PhoneNumberValidator()(value)


class AvailableSlotsSerializer(serializers.Serializer):
    """Serializer for available slots response"""
    
    time = serializers.CharField()
    available = serializers.BooleanField()
    fee = serializers.CharField()


class CancelAppointmentSerializer(serializers.Serializer):
    """Serializer for cancelling appointment"""
    
    reason = serializers.CharField(required=False, allow_blank=True)
