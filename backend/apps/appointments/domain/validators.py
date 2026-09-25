"""Appointment domain validators"""
from django.core.exceptions import ValidationError
from datetime import time


def validate_appointment_time(value: time) -> time:
    """
    Validate appointment time is within working hours.
    Typical working hours: 8:00 - 20:00
    """
    if value.hour < 8 or value.hour >= 20:
        raise ValidationError("زمان نوبت باید بین ۸ صبح تا ۸ شب باشد")
    
    # Validate minutes are in 15-minute intervals
    if value.minute not in [0, 15, 30, 45]:
        raise ValidationError("زمان نوبت باید در بازه‌های ۱۵ دقیقه‌ای باشد")
    
    return value
