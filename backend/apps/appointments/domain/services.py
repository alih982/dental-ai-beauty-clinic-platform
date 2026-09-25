"""
Appointment domain services - Business logic layer
"""
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.services import BaseService, DomainEvent, EventPublisher
from apps.appointments.domain.models import Appointment, TimeSlot
from apps.appointments.infrastructure.repositories import AppointmentRepository


class AppointmentService(BaseService[Appointment]):
    """
    Appointment business logic service.
    
    Responsibilities:
    - Create and manage appointments
    - Validate appointment rules
    - Check slot availability
    - Send notifications
    """
    
    def __init__(self):
        super().__init__(AppointmentRepository())
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate appointment data.
        
        Business rules:
        - Appointment must be in the future
        - Cannot book more than 3 months in advance
        - Must be during doctor's working hours
        - Slot must be available
        """
        from apps.core.validators import RequiredFieldsValidator
        
        # Check required fields
        required = ['doctor_id', 'appointment_date', 'appointment_time', 
                   'patient_name', 'patient_phone']
        RequiredFieldsValidator(required)(data)
        
        # Validate date is in future
        appointment_date = data.get('appointment_date')
        if isinstance(appointment_date, str):
            appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        
        if appointment_date < timezone.now().date():
            raise ValidationError("تاریخ نوبت باید در آینده باشد")
        
        # Can't book more than 3 months ahead
        max_date = timezone.now().date() + timedelta(days=90)
        if appointment_date > max_date:
            raise ValidationError("امکان رزرو نوبت بیش از ۳ ماه آینده وجود ندارد")
        
        return data
    
    async def check_slot_availability(
        self, 
        doctor_id: str, 
        appointment_date: date, 
        appointment_time: time
    ) -> bool:
        """Check if time slot is available"""
        exists = await self.repository.aexists(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
        )
        return not exists
    
    async def get_available_slots(
        self,
        doctor_id: str,
        appointment_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for a doctor on a specific date.
        
        Returns list of available slots with their availability status.
        """
        from apps.doctors.domain.models import Doctor
        
        # Get doctor
        doctor = await Doctor.objects.aget(id=doctor_id)
        
        # Get doctor's time slots for this day
        day_of_week = appointment_date.weekday()
        time_slots = await TimeSlot.objects.filter(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_active=True
        ).alist()
        
        if not time_slots:
            return []
        
        # Get booked appointments for this date
        booked_times = set()
        async for apt in self.repository.filter(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
        ):
            booked_times.add(apt.appointment_time)
        
        # Generate available slots
        available_slots = []
        for slot in time_slots:
            current_time = datetime.combine(appointment_date, slot.start_time)
            end_time = datetime.combine(appointment_date, slot.end_time)
            
            while current_time < end_time:
                slot_time = current_time.time()
                available_slots.append({
                    'time': slot_time.strftime('%H:%M'),
                    'time_obj': slot_time,
                    'available': slot_time not in booked_times,
                    'fee': str(doctor.fee)
                })
                current_time += timedelta(minutes=slot.duration_minutes)
        
        return available_slots
    
    @transaction.atomic
    async def book_appointment(
        self,
        doctor_id: str,
        appointment_date: date,
        appointment_time: time,
        patient_name: str,
        patient_phone: str,
        symptoms: str = None,
        notes: str = None,
        patient_id: str = None,
        auto_activate_chat: bool = False
    ) -> Appointment:
        """
        Book new appointment with all validations.
        
        Steps:
        1. Validate input data
        2. Check slot availability
        3. Get doctor info and fee
        4. Create appointment
        5. Publish event
        6. Send confirmation (async task)
        
        Args:
            auto_activate_chat: If True, automatically activate chat session after booking
                              (useful for instant/online payments)
        """
        from apps.doctors.domain.models import Doctor
        
        # Prepare data
        data = {
            'doctor_id': doctor_id,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'patient_name': patient_name,
            'patient_phone': patient_phone,
            'symptoms': symptoms,
            'notes': notes,
        }
        
        # Validate
        validated_data = self.validate(data)
        
        # Check availability
        is_available = await self.check_slot_availability(
            doctor_id, appointment_date, appointment_time
        )
        if not is_available:
            raise ValidationError("این زمان قبلاً رزرو شده است")
        
        # Get doctor and fee
        doctor = await Doctor.objects.aget(id=doctor_id)
        
        # Create appointment
        appointment = await self.repository.acreate(
            doctor_id=doctor_id,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            fee=doctor.fee,
            symptoms=symptoms or '',
            notes=notes or '',
            status=Appointment.Status.CONFIRMED,
            payment_status='paid'
        )
        
        # Publish event for notification service
        event = DomainEvent(
            event_type='appointment.booked',
            data={
                'appointment_id': str(appointment.id),
                'patient_name': patient_name,
                'patient_phone': patient_phone,
                'doctor_name': doctor.get_full_name(),
                'appointment_date': appointment_date.isoformat(),
                'appointment_time': appointment_time.isoformat(),
            }
        )
        await EventPublisher.publish(event)
        
        # Auto-activate chat session if requested (for instant payments)
        if auto_activate_chat:
            # Use synchronous function to ensure immediate chat activation
            # without depending on Celery worker
            from apps.appointments.tasks import activate_chat_session_sync
            result = activate_chat_session_sync(appointment.id)
            self.logger.info(f"Chat activation result: {result}")
        
        self.logger.info(f"Appointment booked: {appointment.appointment_number}")
        return appointment
    
    async def confirm_payment(self, appointment_id: str) -> Appointment:
        """
        Confirm payment for an appointment and optionally activate chat.
        
        This is called when payment is successfully completed.
        """
        appointment = await self.repository.aget_by_id(appointment_id)
        if not appointment:
            raise ValueError("نوبت یافت نشد")
        
        # Update payment status
        appointment.payment_status = 'paid'
        
        # Update status to confirmed if still pending
        if appointment.status == Appointment.Status.PENDING:
            appointment.status = Appointment.Status.CONFIRMED
        
        await appointment.asave()
        
        # Use synchronous function for immediate chat activation
        from apps.appointments.tasks import activate_chat_session_sync
        result = activate_chat_session_sync(appointment.id)
        self.logger.info(f"Chat activation result: {result}")
        
        # Publish event
        event = DomainEvent(
            event_type='appointment.payment_confirmed',
            data={
                'appointment_id': str(appointment.id),
                'appointment_number': appointment.appointment_number,
            }
        )
        await EventPublisher.publish(event)
        
        return appointment
    
    async def cancel_appointment(self, appointment_id: str, reason: str = None) -> bool:
        """Cancel appointment with validation"""
        appointment = await self.repository.aget_by_id(appointment_id)
        if not appointment:
            raise ValueError("نوبت یافت نشد")
        
        if not appointment.can_cancel():
            raise ValueError("امکان لغو نوبت کمتر از ۲۴ ساعت مانده وجود ندارد")
        
        appointment.status = Appointment.Status.CANCELLED
        if reason:
            appointment.notes = f"{appointment.notes}\nدلیل لغو: {reason}"
        
        await appointment.asave()
        
        # Publish event
        event = DomainEvent(
            event_type='appointment.cancelled',
            data={
                'appointment_id': str(appointment.id),
                'appointment_number': appointment.appointment_number,
            }
        )
        await EventPublisher.publish(event)
        
        return True
    
    async def get_upcoming_appointments(
        self,
        doctor_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        days_ahead: int = 7
    ) -> List[Appointment]:
        """Get upcoming appointments for doctor or patient"""
        filters = {
            'appointment_date__gte': timezone.now().date(),
            'appointment_date__lte': timezone.now().date() + timedelta(days=days_ahead),
            'status__in': [Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
        }
        
        if doctor_id:
            filters['doctor_id'] = doctor_id
        if patient_id:
            filters['patient_id'] = patient_id
        
        return await self.repository.afilter(**filters)
