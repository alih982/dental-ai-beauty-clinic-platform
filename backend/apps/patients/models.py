"""
Enhanced Patient Records Models - FIXED VERSION
==============================
Fixed syntax errors from literal newlines in OneToOneField definitions

Author: Hospital Application
Version: 2.0.0
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class BloodTypeChoices(models.TextChoices):
    A_POSITIVE = 'A+', 'A+'
    A_NEGATIVE = 'A-', 'A-'
    B_POSITIVE = 'B+', 'B+'
    B_NEGATIVE = 'B-', 'B-'
    O_POSITIVE = 'O+', 'O+'
    O_NEGATIVE = 'O-', 'O-'
    AB_POSITIVE = 'AB+', 'AB+'
    AB_NEGATIVE = 'AB-', 'AB-'


class GenderChoices(models.TextChoices):
    MALE = 'male', _('Male')
    FEMALE = 'female', _('Female')
    OTHER = 'other', _('Other')


class PatientStatusChoices(models.TextChoices):
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
    DISCHARGED = 'discharged', _('Discharged')
    DECEASED = 'deceased', _('Deceased')


class MedicalRecordTypeChoices(models.TextChoices):
    DIAGNOSIS = 'diagnosis', _('Diagnosis')
    PRESCRIPTION = 'prescription', _('Prescription')
    LAB_RESULT = 'lab_result', _('Lab Result')
    IMAGING = 'imaging', _('Imaging')
    SURGERY = 'surgery', _('Surgery')
    FOLLOW_UP = 'follow_up', _('Follow Up')
    VITAL_SIGNS = 'vital_signs', _('Vital Signs')
    NOTE = 'note', _('Medical Note')


class PrescriptionStatusChoices(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    ISSUED = 'issued', _('Issued')
    DISPENSED = 'dispensed', _('Dispensed')
    CANCELLED = 'cancelled', _('Cancelled')
    EXPIRED = 'expired', _('Expired')


class InvoiceStatusChoices(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    PENDING = 'pending', _('Pending')
    PAID = 'paid', _('Paid')
    CANCELLED = 'cancelled', _('Cancelled')
    REFUNDED = 'refunded', _('Refunded')


# ============== Patient Profile ==============
class PatientProfile(models.Model):
    """
    Complete patient profile with all medical information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_profiles'
    )
    
    # Basic Information
    record_number = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name=_('Medical Record Number')
    )
    first_name = models.CharField(max_length=100, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=100, verbose_name=_('Last Name'))
    father_name = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Father Name')
    )
    national_id = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name=_('National ID')
    )
    birth_date = models.DateField(verbose_name=_('Birth Date'))
    gender = models.CharField(
        max_length=10, 
        choices=GenderChoices.choices,
        verbose_name=_('Gender')
    )
    
    # Medical Information
    blood_type = models.CharField(
        max_length=5, 
        choices=BloodTypeChoices.choices,
        blank=True,
        verbose_name=_('Blood Type')
    )
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        verbose_name=_('Height (cm)')
    )
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(500)],
        verbose_name=_('Weight (kg)')
    )
    
    # Allergies & Chronic Diseases
    allergies = models.JSONField(
        default=list, 
        blank=True,
        verbose_name=_('Allergies')
    )
    chronic_diseases = models.JSONField(
        default=list, 
        blank=True,
        verbose_name=_('Chronic Diseases')
    )
    family_history = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name=_('Family Medical History')
    )
    surgeries = models.JSONField(
        default=list, 
        blank=True,
        verbose_name=_('Previous Surgeries')
    )
    
    # Current Status
    status = models.CharField(
        max_length=20, 
        choices=PatientStatusChoices.choices,
        default=PatientStatusChoices.ACTIVE,
        verbose_name=_('Status')
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name=_('Emergency Contact Name')
    )
    emergency_contact_phone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name=_('Emergency Contact Phone')
    )
    emergency_contact_relation = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name=_('Relation to Patient')
    )
    
    # Insurance Information
    insurance_provider = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name=_('Insurance Provider')
    )
    insurance_number = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name=_('Insurance Number')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patient_profiles'
        verbose_name = _('Patient Profile')
        verbose_name_plural = _('Patient Profiles')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.record_number} - {self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate patient age"""
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.record_number:
            # Generate unique record number
            last_record = PatientProfile.objects.order_by('-created_at').first()
            if last_record:
                last_num = int(last_record.record_number.replace('PR-', ''))
                self.record_number = f"PR-{last_num + 1:05d}"
            else:
                self.record_number = "PR-00001"
        super().save(*args, **kwargs)


# ============== Medical Record ==============
class MedicalRecord(models.Model):
    """
    Individual medical records for patient visits and follow-ups
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        PatientProfile, 
        on_delete=models.CASCADE, 
        related_name='medical_records'
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='patient_records'
    )
    
    # Record Information
    record_type = models.CharField(
        max_length=20,
        choices=MedicalRecordTypeChoices.choices,
        verbose_name=_('Record Type')
    )
    title = models.CharField(
        max_length=200, 
        verbose_name=_('Title')
    )
    description = models.TextField(verbose_name=_('Description'))
    
    # Clinical Data
    chief_complaint = models.TextField(
        blank=True,
        verbose_name=_('Chief Complaint')
    )
    symptoms = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Symptoms')
    )
    diagnosis = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Diagnosis')
    )
    
    # Vital Signs
    vital_signs = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Vital Signs')
    )
    # Example: {"blood_pressure": "120/80", "heart_rate": 72, "temperature": 37, "spo2": 98}
    
    # Treatment Plan
    treatment_plan = models.TextField(
        blank=True,
        verbose_name=_('Treatment Plan')
    )
    recommendations = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Recommendations')
    )
    
    # Attachments
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Attachments (Lab results, imaging URLs)')
    )
    
    # Follow-up
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Follow-up Date')
    )
    follow_up_notes = models.TextField(
        blank=True,
        verbose_name=_('Follow-up Notes')
    )
    
    # Digital Signature
    digital_signature = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Digital Signature Hash')
    )
    is_signed = models.BooleanField(default=False)
    
    # Timestamps
    visit_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_records'
        verbose_name = _('Medical Record')
        verbose_name_plural = _('Medical Records')
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.title}"


# ============== Electronic Prescription ==============
class ElectronicPrescription(models.Model):
    """
    Digital prescription with full medication details
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='electronic_prescriptions'
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_prescriptions'
    )
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescriptions'
    )
    
    # Prescription Details
    prescription_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Prescription Number')
    )
    diagnosis = models.TextField(
        blank=True,
        verbose_name=_('Diagnosis')
    )
    status = models.CharField(
        max_length=20,
        choices=PrescriptionStatusChoices.choices,
        default=PrescriptionStatusChoices.ISSUED,
        verbose_name=_('Status')
    )
    
    # Medication Instructions
    instructions = models.TextField(
        blank=True,
        verbose_name=_('General Instructions')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Additional Notes')
    )
    
    # Validity
    issue_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateField(
        verbose_name=_('Expiry Date')
    )
    valid_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Valid for (days)')
    )
    
    # Digital Signature
    digital_signature = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Digital Signature')
    )
    signature_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Signature Timestamp')
    )
    
    # Dispensing Information
    dispensed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Dispensed At')
    )
    pharmacy_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Dispensing Pharmacy')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'electronic_prescriptions'
        verbose_name = _('Electronic Prescription')
        verbose_name_plural = _('Electronic Prescriptions')
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.prescription_number} - {self.patient.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            last_rx = ElectronicPrescription.objects.order_by('-created_at').first()
            if last_rx:
                last_num = int(last_rx.prescription_number.replace('RX-', ''))
                self.prescription_number = f"RX-{last_num + 1:06d}"
            else:
                self.prescription_number = "RX-000001"
        
        if not self.expiry_date:
            from datetime import timedelta
            self.expiry_date = timezone.now().date() + timedelta(days=self.valid_days)
        
        super().save(*args, **kwargs)
    
    def generate_pdf(self):
        """Generate PDF for the prescription"""
        from .pdf_generator import PrescriptionPDFGenerator
        generator = PrescriptionPDFGenerator()
        return generator.generate(self)


class PrescriptionItem(models.Model):
    """
    Individual medication items in a prescription
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(
        ElectronicPrescription,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Medication Details
    medication_name = models.CharField(
        max_length=200,
        verbose_name=_('Medication Name')
    )
    medication_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Medication Code (NDC)')
    )
    
    # Dosage
    dosage = models.CharField(
        max_length=100,
        verbose_name=_('Dosage (e.g., 500mg)')
    )
    frequency = models.CharField(
        max_length=100,
        verbose_name=_('Frequency (e.g., 2x daily)')
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Duration (e.g., 7 days)')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Quantity')
    )
    
    # Instructions
    instructions = models.TextField(
        blank=True,
        verbose_name=_('Specific Instructions')
    )
    
    # Substitutions
    allow_substitution = models.BooleanField(
        default=True,
        verbose_name=_('Allow Generic Substitution')
    )
    
    # Dispensing Status
    is_dispensed = models.BooleanField(default=False)
    dispensed_quantity = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'prescription_items'
        verbose_name = _('Prescription Item')
        verbose_name_plural = _('Prescription Items')
    
    def __str__(self):
        return f"{self.medication_name} - {self.dosage}"


# ============== Invoice ==============
class Invoice(models.Model):
    """
    Medical invoice with detailed billing
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    prescription = models.ForeignKey(
        ElectronicPrescription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    
    # Invoice Details
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Invoice Number')
    )
    invoice_type = models.CharField(
        max_length=50,
        choices=[
            ('consultation', _('Consultation')),
            ('prescription', _('Prescription')),
            ('lab', _('Lab Test')),
            ('imaging', _('Imaging')),
            ('procedure', _('Procedure')),
            ('other', _('Other'))
        ],
        verbose_name=_('Invoice Type')
    )
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatusChoices.choices,
        default=InvoiceStatusChoices.DRAFT,
        verbose_name=_('Status')
    )
    
    # Description
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    # Financial
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Subtotal')
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Discount')
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Tax')
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total')
    )
    
    # Insurance
    insurance_coverage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Insurance Coverage (%)')
    )
    insurance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Insurance Amount')
    )
    patient_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Patient Pay')
    )
    
    # Payment
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('cash', _('Cash')),
            ('card', _('Card')),
            ('insurance', _('Insurance')),
            ('online', _('Online'))
        ],
        verbose_name=_('Payment Method')
    )
    payment_reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Payment Reference')
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Paid At')
    )
    
    # Timestamps
    issue_date = models.DateTimeField(default=timezone.now())
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Due Date')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.patient.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_inv = Invoice.objects.order_by('-created_at').first()
            if last_inv:
                last_num = int(last_inv.invoice_number.replace('INV-', ''))
                self.invoice_number = f"INV-{last_num + 1:06d}"
            else:
                self.invoice_number = "INV-000001"
        
        # Calculate totals
        self.total = self.subtotal - self.discount + self.tax
        self.insurance_amount = (self.total * self.insurance_coverage) / 100
        self.patient_pay = self.total - self.insurance_amount
        
        super().save(*args, **kwargs)
    
    def generate_pdf(self):
        """Generate PDF for the invoice"""
        from .pdf_generator import InvoicePDFGenerator
        generator = InvoicePDFGenerator()
        return generator.generate(self)


class InvoiceItem(models.Model):
    """
    Individual line items in an invoice
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Item Details
    description = models.CharField(
        max_length=500,
        verbose_name=_('Description')
    )
    service_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Service Code')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity')
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Unit Price')
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Discount')
    )
    
    @property
    def total(self):
        return (self.unit_price * self.quantity) - self.discount
    
    class Meta:
        db_table = 'invoice_items'
        verbose_name = _('Invoice Item')
        verbose_name_plural = _('Invoice Items')
    
    def __str__(self):
        return f"{self.description} - {self.total}"


# ============== Symptom Tracking ==============
class SymptomLog(models.Model):
    """
    Patient symptom tracking over time
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='symptom_logs'
    )
    
    # Symptom Details
    symptom_name = models.CharField(
        max_length=200,
        verbose_name=_('Symptom')
    )
    severity = models.PositiveIntegerField(
        choices=[
            (1, _('Mild')),
            (2, _('Moderate')),
            (3, _('Severe')),
            (4, _('Critical'))
        ],
        verbose_name=_('Severity')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    # Timing
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Started At')
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Ended At')
    )
    is_ongoing = models.BooleanField(default=True)
    
    # Triggers & Relief
    triggers = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Triggers')
    )
    relief_methods = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Relief Methods')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'symptom_logs'
        verbose_name = _('Symptom Log')
        verbose_name_plural = _('Symptom Logs')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.symptom_name}"




