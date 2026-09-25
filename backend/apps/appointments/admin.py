"""Appointments admin"""
from django.contrib import admin
from apps.appointments.domain.models import Appointment, TimeSlot


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_number', 'patient_name', 'doctor', 'appointment_date', 
                    'appointment_time', 'status', 'created_at']
    list_filter = ['status', 'appointment_date', 'payment_status']
    search_fields = ['appointment_number', 'patient_name', 'patient_phone']
    readonly_fields = ['appointment_number', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('اطلاعات پزشک و بیمار', {
            'fields': ('doctor', 'patient', 'patient_name', 'patient_phone')
        }),
        ('اطلاعات نوبت', {
            'fields': ('appointment_date', 'appointment_time', 'appointment_number', 'status')
        }),
        ('اطلاعات مالی', {
            'fields': ('fee', 'payment_status')
        }),
        ('اطلاعات اضافی', {
            'fields': ('symptoms', 'notes', 'reminder_sent')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'duration_minutes', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['doctor__first_name', 'doctor__last_name']
