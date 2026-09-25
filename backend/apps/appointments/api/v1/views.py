"""
Async API Views for Appointments - v1
Using async_to_sync for compatibility with standard DRF
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import ValidationError
from asgiref.sync import async_to_sync
from datetime import datetime

from apps.appointments.domain.services import AppointmentService
from apps.appointments.infrastructure.serializers import (
    AppointmentSerializer,
    BookAppointmentSerializer,
    AvailableSlotsSerializer,
    CancelAppointmentSerializer
)


class AppointmentViewSet(viewsets.ViewSet):
    """
    ViewSet for Appointment operations.
    Uses async_to_sync to bridge between sync DRF and async Service layer.
    """
    
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]
    
    # Separate permission for authenticated endpoints
    def get_permissions(self):
        if self.action in ['get_doctor_patients']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = AppointmentService()
    
    def list(self, request):
        """
        List appointments with filters.
        """
        filters = {}
        
        if doctor_id := request.query_params.get('doctor_id'):
            filters['doctor_id'] = doctor_id
        
        if patient_id := request.query_params.get('patient_id'):
            filters['patient_id'] = patient_id
        
        if apt_status := request.query_params.get('status'):
            filters['status'] = apt_status
        
        if apt_date := request.query_params.get('date'):
            try:
                filters['appointment_date'] = datetime.strptime(apt_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Bridge to async service
        appointments = async_to_sync(self.service.alist_all)(**filters)
        serializer = AppointmentSerializer(appointments, many=True)
        
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get single appointment by ID"""
        appointment = async_to_sync(self.service.aget_by_id)(pk)
        
        if not appointment:
            return Response(
                {'detail': 'نوبت یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='book')
    def book_appointment(self, request):
        """
        Book a new appointment.
        """
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            kwargs = serializer.validated_data.copy()
            kwargs['auto_activate_chat'] = True
            kwargs['patient_id'] = getattr(request.user.patient_profile, 'id', None) if hasattr(request.user, 'patient_profile') else None

            appointment = async_to_sync(self.service.book_appointment)(**kwargs)
            
            response_serializer = AppointmentSerializer(appointment)
            return Response(
                {
                    'success': True,
                    'message': 'نوبت با موفقیت رزرو شد',
                    'data': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': 'خطای سیستمی رخ داده است'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request):
        """
        Get available time slots.
        """
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')
        
        if not doctor_id or not date_str:
            return Response(
                {'detail': 'doctor_id و date الزامی هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slots = async_to_sync(self.service.get_available_slots)(doctor_id, appointment_date)
            
            serializer = AvailableSlotsSerializer(slots, many=True)
            return Response({
                'success': True,
                'date': date_str,
                'slots': serializer.data
            })
        
        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel an appointment.
        """
        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            async_to_sync(self.service.cancel_appointment)(
                pk,
                reason=serializer.validated_data.get('reason')
            )
            
            return Response({
                'success': True,
                'message': 'نوبت با موفقیت لغو شد'
            })
        
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request):
        """
        Get upcoming appointments.
        """
        doctor_id = request.query_params.get('doctor_id')
        patient_id = request.query_params.get('patient_id')
        days_ahead = int(request.query_params.get('days', 7))
        
        appointments = async_to_sync(self.service.get_upcoming_appointments)(
            doctor_id=doctor_id,
            patient_id=patient_id,
            days_ahead=days_ahead
        )
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response({
            'success': True,
            'count': len(appointments),
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='confirm-payment')
    def confirm_payment(self, request, pk=None):
        """
        Confirm payment for an appointment and activate chat session.
        
        This endpoint should be called after successful payment.
        """
        try:
            appointment = async_to_sync(self.service.confirm_payment)(pk)
            serializer = AppointmentSerializer(appointment)
            
            return Response({
                'success': True,
                'message': 'Payment confirmed and chat session activated',
                'data': serializer.data
            })
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': 'خطای سیستمی رخ داده است'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='patients')
    def get_doctor_patients(self, request):
        """
        Get all unique patients who have appointments with the authenticated doctor.
        """
        from apps.appointments.domain.models import Appointment
        from apps.patients.models import Patient
        from django.db.models import Count
        
        # Get the doctor from the authenticated user
        from apps.doctors.models import Doctor
        doctor = None
        
        if hasattr(request.user, 'doctor_profile'):
            doctor = request.user.doctor_profile
        else:
            try:
                doctor = Doctor.objects.get(user=request.user)
            except Doctor.DoesNotExist:
                return Response(
                    {'success': False, 'message': 'Doctor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get unique patients from appointments
        patient_ids = Appointment.objects.filter(
            doctor=doctor
        ).values_list('patient', flat=True).distinct()
        
        patients = Patient.objects.filter(id__in=patient_ids).select_related('user')
        
        # Serialize patient data
        patient_data = []
        for patient in patients:
            user = patient.user
            patient_data.append({
                'id': str(patient.id),
                'full_name': user.get_full_name() if user else patient.phone,
                'phone': patient.phone,
                'email': user.email if user else None,
                'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            })
        
        return Response({
            'success': True,
            'count': len(patient_data),
            'data': patient_data
        })
