from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers
from asgiref.sync import async_to_sync
from apps.patients.domain.services import PatientService


class PatientSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user = serializers.StringRelatedField()
    phone = serializers.CharField()
    date_of_birth = serializers.DateField()
    gender = serializers.CharField()
    blood_type = serializers.CharField()
    emergency_contact = serializers.CharField()
    emergency_phone = serializers.CharField()


class PatientViewSet(viewsets.ViewSet):
    serializer_class = PatientSerializer
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = PatientService()
    
    def list(self, request):
        """Get list of patients - requires authentication"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Return empty list for now - this endpoint is mainly for doctors/admin
        return Response([])

    def retrieve(self, request, pk=None):
        """Get patient details including medical data"""
        try:
            patient_data = async_to_sync(self.service.get_patient_with_medical_data)(pk)
            return Response(patient_data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='appointments')
    def appointments(self, request, pk=None):
        """Get patient appointment history"""
        appointments = async_to_sync(self.service.get_patient_appointments)(pk)
        return Response([
            {
                'id': str(a.id),
                'doctor_name': a.doctor.get_full_name(),
                'date': a.appointment_date,
                'time': a.appointment_time,
                'status': a.status
            } for a in appointments
        ])

    @action(detail=True, methods=['post'], url_path='add-history')
    def add_history(self, request, pk=None):
        """Add a medical history entry for the patient"""
        condition = request.data.get('condition')
        diagnosis_date = request.data.get('diagnosis_date')
        notes = request.data.get('notes', '')
        
        if not condition:
            return Response({'detail': 'Condition name is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        entry = async_to_sync(self.service.add_medical_history)(
            pk, condition, diagnosis_date, notes
        )
        return Response({'id': str(entry.id), 'condition': entry.condition}, status=status.HTTP_201_CREATED)
