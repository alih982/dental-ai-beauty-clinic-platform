"""
Appointment infrastructure layer - repositories
"""
from apps.core.repositories import BaseRepository
from apps.appointments.domain.models import Appointment, TimeSlot


class AppointmentRepository(BaseRepository[Appointment]):
    """Repository for Appointment aggregate"""
    
    def __init__(self):
        super().__init__(Appointment)
    
    def get_queryset(self):
        """Optimize queries with select_related"""
        return super().get_queryset().select_related('doctor', 'patient')


class TimeSlotRepository(BaseRepository[TimeSlot]):
    """Repository for TimeSlot entity"""
    
    def __init__(self):
        super().__init__(TimeSlot)
    
    def get_queryset(self):
        """Only active slots by default"""
        return super().get_queryset().filter(is_active=True).select_related('doctor')
