from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ...domain.models import Prescription
from ...application.services import ElectronicPrescriptionService
from .serializers import (
    PrescriptionSerializer, 
    AISuggestionRequestSerializer, 
    CreatePrescriptionSerializer
)
# Assuming typical linkage for Doctor/Patient profiles logic exists or will be mocked for now
# from apps.doctors.models import Doctor
# from apps.patients.models import Patient

class PrescriptionViewSet(viewsets.ModelViewSet):

    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Prescription.objects.none()
            
        if hasattr(user, 'doctor_profile'):
            return Prescription.objects.filter(doctor=user.doctor_profile)
        elif hasattr(user, 'patient_profile'):
            return Prescription.objects.filter(patient=user.patient_profile)
        elif user.is_staff or user.is_superuser:
             return Prescription.objects.all()
             
        # Fallback for now: empty or maybe check just ID if simpler model
        return Prescription.objects.none()

    def get_service(self):
        return ElectronicPrescriptionService()

    @action(detail=False, methods=['post'], url_path='ai-suggest')
    def suggest_medication(self, request):
        """
        Endpoint to get AI suggestions for medications based on symptoms.
        """
        serializer = AISuggestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        try:
            suggestion = service.generate_ai_suggestions(
                symptoms=serializer.validated_data['symptoms'],
                medical_history=serializer.validated_data.get('medical_history', "")
            )
            return Response({"suggestion": suggestion}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """
        Custom create method to use the Domain Service for secure creation.
        """
        serializer = CreatePrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Resolve Doctor and Patient from the authenticated user
        try:
            from apps.doctors.models import Doctor
            from apps.patients.models import Patient
            
            # Get doctor from the authenticated user
            doctor = getattr(request.user, 'doctor_profile', None)
            if not doctor:
                # Try to get from Doctor model directly
                try:
                    doctor = Doctor.objects.get(user=request.user)
                except Doctor.DoesNotExist:
                    return Response(
                        {"error": "User is not associated with a doctor profile"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
            patient = get_object_or_404(Patient, id=data['patient_id'])
            
            service = self.get_service()
            prescription = service.create_prescription(
                doctor=doctor,
                patient=patient,
                medications=data['medications'],
                diagnosis=data['diagnosis'],
                ai_log=data.get('ai_log')
            )
            
            response_serializer = PrescriptionSerializer(prescription)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
