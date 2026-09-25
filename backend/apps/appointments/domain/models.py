"""
Appointments Domain Models
Following Clean Architecture and DDD principles
"""
from django.db import models
from apps.core.models import BaseModel
from apps.core.validators import PhoneNumberValidator, RequiredFieldsValidator


class Appointment(BaseModel):
    """
    Appointment aggregate root.
    Represents a patient appointment with a doctor.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار'
        CONFIRMED = 'confirmed', 'تأیید شده'
        CANCELLED = 'cancelled', 'لغو شده'
        COMPLETED = 'completed', 'تکمیل شده'
        NO_SHOW = 'no_show', 'عدم حضور'
    
    # Relations
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='پزشک'
    )
    
    patient = models.ForeignKey(
'patients.PatientProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name='بیمار'
    )
    
    # Chat Session - Links appointment to a conversation
    conversation = models.ForeignKey(
        'chat.Conversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name='گفتگو'
    )
    
    # Patient information (for guest bookings)
    patient_name = models.CharField(
        max_length=255,
        verbose_name='نام بیمار'
    )
    
    patient_phone = models.CharField(
        max_length=15,
        verbose_name='شماره تماس',
        validators=[PhoneNumberValidator()]
    )
    
    # Appointment details
    appointment_date = models.DateField(
        verbose_name='تاریخ نوبت',
        db_index=True
    )
    
    appointment_time = models.TimeField(
        verbose_name='زمان نوبت',
        db_index=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='وضعیت',
        db_index=True
    )
    
    # Financial
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='هزینه ویزیت',
        help_text='به تومان'
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'در انتظار پرداخت'),
            ('paid', 'پرداخت شده'),
            ('refunded', 'بازگشت داده شده'),
        ],
        default='pending',
        verbose_name='وضعیت پرداخت'
    )
    
    # Additional info
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='توضیحات'
    )
    
    symptoms = models.TextField(
        blank=True,
        null=True,
        verbose_name='علائم'
    )
    
    appointment_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره نوبت',
        db_index=True
    )
    
    # Notifications
    reminder_sent = models.BooleanField(
        default=False,
        verbose_name='یادآوری ارسال شده'
    )
    
    class Meta:
        db_table = 'appointments'
        verbose_name = 'نوبت'
        verbose_name_plural = 'نوبت‌ها'
        ordering = ['-appointment_date', '-appointment_time']
        unique_together = [['doctor', 'appointment_date', 'appointment_time']]
        indexes = [
            models.Index(fields=['doctor', 'appointment_date']),
            models.Index(fields=['status', 'appointment_date']),
        ]
    
    def __str__(self):
        return f"{self.appointment_number} - {self.patient_name} - {self.doctor.get_full_name_fa()}"
    
    def save(self, *args, **kwargs):
        """Generate appointment number if not exists"""
        if not self.appointment_number:
            import random
            import string
            # Format: APT-YYYYMMDD-XXXXX
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.digits, k=5))
            self.appointment_number = f"APT-{date_str}-{random_str}"
        
        super().save(*args, **kwargs)
    
    def can_cancel(self):
        """Check if appointment can be cancelled"""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.status in [self.Status.CANCELLED, self.Status.COMPLETED]:
            return False
        
        # Can't cancel within 24 hours
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        return appointment_datetime - timezone.now() > timedelta(hours=24)
    
    def confirm(self):
        """Confirm the appointment"""
        self.status = self.Status.CONFIRMED
        self.save()
    
    def cancel(self):
        """Cancel the appointment"""
        if not self.can_cancel():
            raise ValueError("Cannot cancel appointment within 24 hours")
        self.status = self.Status.CANCELLED
        self.save()
    
    def complete(self):
        """Mark appointment as completed"""
        self.status = self.Status.COMPLETED
        self.save()


class TimeSlot(BaseModel):
    """
    Available time slots for doctors.
    Defines doctor working hours.
    """
    
    class DayOfWeek(models.IntegerChoices):
        SUNDAY = 0, 'یکشنبه'
        MONDAY = 1, 'دوشنبه'
        TUESDAY = 2, 'سه‌شنبه'
        WEDNESDAY = 3, 'چهارشنبه'
        THURSDAY = 4, 'پنجشنبه'
        FRIDAY = 5, 'جمعه'
        SATURDAY = 6, 'شنبه'
    
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name='پزشک'
    )
    
    day_of_week = models.IntegerField(
        choices=DayOfWeek.choices,
        verbose_name='روز هفته'
    )
    
    start_time = models.TimeField(
        verbose_name='زمان شروع'
    )
    
    end_time = models.TimeField(
        verbose_name='زمان پایان'
    )
    
    duration_minutes = models.IntegerField(
        default=30,
        verbose_name='مدت هر نوبت (دقیقه)'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        db_table = 'appointment_time_slots'
        verbose_name = 'بازه زمانی'
        verbose_name_plural = 'بازه‌های زمانی'
        unique_together = [['doctor', 'day_of_week', 'start_time']]
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"
