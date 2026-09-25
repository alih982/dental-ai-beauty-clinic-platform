from rest_framework import serializers
from ...domain.models import Prescription

class MedicationItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    dosage = serializers.CharField(max_length=100)
    frequency = serializers.CharField(max_length=100)
    duration = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

class PrescriptionSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.first_name', read_only=True) # Adjust based on Patient model
    formatted_date = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M", read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'doctor', 'patient', 'doctor_name', 'patient_name',
            'diagnosis_text', 'medications', 'digital_signature', 
            'pdf_file', 'is_dispensed', 'created_at', 'formatted_date'
        ]
        read_only_fields = ['id', 'digital_signature', 'pdf_file', 'created_at']

class AISuggestionRequestSerializer(serializers.Serializer):
    symptoms = serializers.CharField(required=True)
    medical_history = serializers.CharField(required=False, allow_blank=True)

class CreatePrescriptionSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    diagnosis = serializers.CharField()
    medications = MedicationItemSerializer(many=True)
    ai_log = serializers.JSONField(required=False)
