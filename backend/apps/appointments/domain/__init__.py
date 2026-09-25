"""Domain package initialization"""
from .models import Appointment, TimeSlot
from .services import AppointmentService

__all__ = ['Appointment', 'TimeSlot', 'AppointmentService']
