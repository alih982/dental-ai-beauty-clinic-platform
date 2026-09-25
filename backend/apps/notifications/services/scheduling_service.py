"""
Appointment Scheduling Service with Time Management

Advanced scheduling system with:
- Conflict detection
- Reminder scheduling
- WhatsApp notifications
- Calendar export
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import asyncio

from django.utils import timezone
from celery import shared_task

from ..models import Appointment
from .whatsapp_service import whatsapp_service, MessageType


class AppointmentStatus(str, Enum):
    """Appointment status types"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


@dataclass
class TimeSlot:
    """Time slot entity"""
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    appointment_id: Optional[int] = None


class SchedulingService:
    """
    Advanced appointment scheduling service.
    
    Features:
    - Smart conflict detection
    - Automated reminders (24h, 2h before)
    - WhatsApp notifications
    - Doctor availability management
    """
    
    def __init__(self):
        self.reminder_times = [
            timedelta(hours=24),  # 24 hours before
            timedelta(hours=2),   # 2 hours before
        ]
    
    async def schedule_appointment(
        self,
        patient_id: int,
        doctor_id: int,
        start_time: datetime,
        duration_minutes: int = 30,
        notes: Optional[str] = None
    ) -> dict:
        """
        Schedule a new appointment.
        
        Args:
            patient_id: Patient ID
            doctor_id: Doctor ID
            start_time: Appointment start time
            duration_minutes: Duration in minutes
            notes: Additional notes
            
        Returns:
            Appointment details and scheduling result
        """
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Check for conflicts
        has_conflict = await self.check_conflict(doctor_id, start_time, end_time)
        if has_conflict:
            return {
                "success": False,
                "error": "Time slot not available",
                "suggested_slots": await self.get_available_slots(doctor_id, start_time.date())
            }
        
        # Create appointment (simplified - actual implementation uses repository pattern)
        from apps.appointments.domain.models import Appointment as AppointmentModel
        
        appointment = AppointmentModel.objects.create(
            patient_id=patient_id,
            doctor_id=doctor_id,
            scheduled_time=start_time,
            duration_minutes=duration_minutes,
            status=AppointmentStatus.SCHEDULED.value,
            notes=notes or ""
        )
        
        # Schedule reminders
        await self.schedule_reminders(appointment)
        
        # Send confirmation
        await self.send_confirmation(appointment)
        
        return {
            "success": True,
            "appointment_id": appointment.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "status": AppointmentStatus.SCHEDULED.value
        }
    
    async def check_conflict(
        self,
        doctor_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check for scheduling conflicts.
        
        Args:
            doctor_id: Doctor ID
            start_time: Proposed start time
            end_time: Proposed end time
            
        Returns:
            True if conflict exists
        """
        from apps.appointments.domain.models import Appointment as AppointmentModel
        
        conflicts = AppointmentModel.objects.filter(
            doctor_id=doctor_id,
            scheduled_time__lt=end_time,
            scheduled_time__gte=start_time,
            status__in=[AppointmentStatus.SCHEDULED.value, AppointmentStatus.CONFIRMED.value]
        ).exists()
        
        return conflicts
    
    async def get_available_slots(
        self,
        doctor_id: int,
        date: datetime.date,
        slot_duration: int = 30
    ) -> List[TimeSlot]:
        """
        Get available time slots for a doctor on a specific date.
        
        Args:
            doctor_id: Doctor ID
            date: Target date
            slot_duration: Slot duration in minutes
            
        Returns:
            List of available time slots
        """
        # Define working hours (8 AM - 5 PM)
        working_start = datetime.combine(date, datetime.min.time()).replace(hour=8)
        working_end = datetime.combine(date, datetime.min.time()).replace(hour=17)
        
        # Get existing appointments
        from apps.appointments.domain.models import Appointment as AppointmentModel
        
        existing = list(AppointmentModel.objects.filter(
            doctor_id=doctor_id,
            scheduled_time__date=date,
            status__in=[AppointmentStatus.SCHEDULED.value, AppointmentStatus.CONFIRMED.value]
        ).values_list('scheduled_time', 'duration_minutes'))
        
        # Generate all possible slots
        slots = []
        current = working_start
        
        while current < working_end:
            slot_end = current + timedelta(minutes=slot_duration)
            
            # Check if slot conflicts with any appointment
            is_available = True
            for appt_start, duration in existing:
                appt_end = appt_start + timedelta(minutes=duration)
                if current < appt_end and slot_end > appt_start:
                    is_available = False
                    break
            
            slots.append(TimeSlot(
                start_time=current,
                end_time=slot_end,
                is_available=is_available
            ))
            
            current = slot_end
        
        # Return only available slots
        return [slot for slot in slots if slot.is_available]
    
    async def schedule_reminders(self, appointment) -> None:
        """
        Schedule automated reminders for appointment.
        
        Args:
            appointment: Appointment instance
        """
        for reminder_delta in self.reminder_times:
            reminder_time = appointment.scheduled_time - reminder_delta
            
            # Don't schedule past reminders
            if reminder_time > timezone.now():
                # Schedule Celery task
                send_appointment_reminder.apply_async(
                    args=[appointment.id],
                    eta=reminder_time
                )
    
    async def send_confirmation(self, appointment) -> None:
        """Send appointment confirmation via WhatsApp"""
        if whatsapp_service.is_active:
            await whatsapp_service.send_appointment_reminder(
                phone_number=appointment.patient.user.phone_number,
                doctor_name=f"Dr. {appointment.doctor.user.get_full_name()}",
                appointment_date=appointment.scheduled_time.strftime("%Y-%m-%d"),
                appointment_time=appointment.scheduled_time.strftime("%H:%M")
            )
    
    async def cancel_appointment(
        self,
        appointment_id: int,
        reason: Optional[str] = None
    ) -> dict:
        """
        Cancel an appointment.
        
        Args:
            appointment_id: Appointment ID
            reason: Cancellation reason
            
        Returns:
            Cancellation result
        """
        from apps.appointments.domain.models import Appointment as AppointmentModel
        
        try:
            appointment = AppointmentModel.objects.get(id=appointment_id)
            appointment.status = AppointmentStatus.CANCELLED.value
            appointment.cancellation_reason = reason
            appointment.save()
            
            # Notify patient
            if whatsapp_service.is_active:
                await whatsapp_service.send_message({
                    "phone_number": appointment.patient.user.phone_number,
                    "message_type": MessageType.GENERAL_NOTIFICATION,
                    "content": f"نوبت شما در تاریخ {appointment.scheduled_time.strftime('%Y-%m-%d')} لغو شد.\n\nدلیل: {reason or 'نامشخص'}"
                })
            
            return {"success": True, "appointment_id": appointment_id}
            
        except AppointmentModel.DoesNotExist:
            return {"success": False, "error": "Appointment not found"}


# Celery task for sending reminders
@shared_task
def send_appointment_reminder(appointment_id: int):
    """
    Celery task to send appointment reminder.
    
    This runs asynchronously at scheduled time.
    """
    from apps.appointments.domain.models import Appointment as AppointmentModel
    
    try:
        appointment = AppointmentModel.objects.get(id=appointment_id)
        
        # Send WhatsApp reminder
        if whatsapp_service.is_active:
            asyncio.run(whatsapp_service.send_appointment_reminder(
                phone_number=appointment.patient.user.phone_number,
                doctor_name=f"Dr. {appointment.doctor.user.get_full_name()}",
                appointment_date=appointment.scheduled_time.strftime("%Y-%m-%d"),
                appointment_time=appointment.scheduled_time.strftime("%H:%M")
            ))
        
        return {"status": "sent", "appointment_id": appointment_id}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# Singleton instance
scheduling_service = SchedulingService()
