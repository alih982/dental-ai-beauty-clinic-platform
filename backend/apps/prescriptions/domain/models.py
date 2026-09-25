from django.db import models
from apps.core.models import BaseModel
import uuid

class Prescription(BaseModel):
    """
    Electronic Prescription Entity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    doctor = models.ForeignKey(
        'doctors.Doctor', 
        related_name='prescriptions', 
        on_delete=models.PROTECT,
        verbose_name='پزشک'
    )
    patient = models.ForeignKey(
        'patients.PatientProfile', 
        related_name='prescription_simple', 
        on_delete=models.PROTECT,
        verbose_name='بیمار'
    )
    
    # Medical Context
    diagnosis_text = models.TextField(verbose_name='تشخیص')
    ai_suggestion_log = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='لاگ هوش مصنوعی'
    )
    
    # Medication Items (Stored as JSON for flexibility, can be normalized later)
    medications = models.JSONField(verbose_name='داروها')
    
    # Security & Documents
    digital_signature = models.CharField(max_length=255, verbose_name='امضای دیجیتال')
    pdf_file = models.FileField(
        upload_to='prescriptions/secure/', 
        null=True, 
        blank=True,
        verbose_name='فایل نسخه'
    )
    
    # Status
    is_dispensed = models.BooleanField(default=False, verbose_name='تحویل داده شده')
    
    class Meta:
        db_table = 'prescriptions'
        verbose_name = 'نسخه الکترونیک'
        verbose_name_plural = 'نسخه‌های الکترونیک'
        ordering = ['-created_at']

    def __str__(self):
        return f"RX-{str(self.id)[:8]}"
