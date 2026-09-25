from django.db import models
from apps.patients.models import PatientProfile as Patient
from apps.doctors.models import Doctor

class MedicalReport(models.Model):
    REPORT_TYPES = [
        ('HEALTH_SUMMARY', 'Health Summary'),
        ('CARDIAC_ANALYSIS', 'Cardiac Analysis'),
        ('LAB_RESULTS', 'Lab Results'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_reports')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='reports/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)
    is_signed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.patient.user.phone_number}"
