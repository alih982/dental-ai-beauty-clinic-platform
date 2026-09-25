"""Appointments app configuration"""
from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.appointments'
    verbose_name = 'نوبت‌ها'
    
    def ready(self):
        """Import signals when app is ready"""
        # Import signals here if needed
        pass
