"""
Patient Domain Models
Patient profiles and medical history
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.core.validators import PhoneNumberValidator, NationalCodeValidator


class Patient(BaseModel):
    """Patient profiles with medical history"""
    
    class Gender(models.TextChoices):
        MALE = 'M', 'مرد'
        FEMALE = 'F', 'زن'
        OTHER = 'O', 'سایر'
    
    class BloodType(models.TextChoices):
        A_POS = 'A+', 'A+'
        A_NEG = 'A-', 'A-'
        B_POS = 'B+', 'B+'
        B_NEG = 'B-', 'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'
        O_POS = 'O+', 'O+'
        O_NEG = 'O-', 'O-'
    
    # Link to User (if registered)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_profile',
        verbose_name='کاربر'
    )
    
    # Personal Information
    first_name = models.CharField(
        max_length=100,
        verbose_name='نام'
    )
    
    last_name = models.CharField(
        max_length=100,
        verbose_name='نام خانوادگی'
    )
    
    national_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[NationalCodeValidator()],
        verbose_name='کد ملی'
    )
    
    phone = models.CharField(
        max_length=15,
        validators=[PhoneNumberValidator()],
        verbose_name='شماره تماس',
        unique=True
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='ایمیل'
    )
    
    date_of_birth = models.DateField(
        verbose_name='تاریخ تولد'
    )
    
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        verbose_name='جنسیت'
    )
    
    # Address
    city = models.CharField(
        max_length=100,
        verbose_name='شهر'
    )
    
    address = models.TextField(
        verbose_name='آدرس'
    )
    
    # Medical Information
    blood_type = models.CharField(
        max_length=3,
        choices=BloodType.choices,
        blank=True,
        verbose_name='گروه خونی'
    )
    
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='قد (سانتی‌متر)'
    )
    
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='وزن (کیلوگرم)'
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='نام تماس اضطراری'
    )
    
    emergency_contact_phone = models.CharField(
        max_length=15,
        validators=[PhoneNumberValidator()],
        blank=True,
        verbose_name='شماره تماس اضطراری'
    )
    
    emergency_contact_relation = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نسبت'
    )
    
    # Profile
    profile_image = models.ImageField(
        upload_to='patients/profiles/',
        blank=True,
        null=True,
        verbose_name='تصویر پروفایل'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        db_table = 'patients'
        verbose_name = 'بیمار'
        verbose_name_plural = 'بیماران'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.get_full_name()
    
    def get_full_name(self):
        """Get patient's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate patient's age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class MedicalHistory(BaseModel):
    """Patient medical history records"""
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_history',
        verbose_name='بیمار'
    )
    
    condition = models.CharField(
        max_length=255,
        verbose_name='بیماری/وضعیت'
    )
    
    diagnosis_date = models.DateField(
        verbose_name='تاریخ تشخیص'
    )
    
    treatment = models.TextField(
        blank=True,
        verbose_name='درمان'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        db_table = 'medical_history'
        verbose_name = 'سابقه پزشکی'
        verbose_name_plural = 'سوابق پزشکی'
        ordering = ['-diagnosis_date']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.condition}"


class Allergy(BaseModel):
    """Patient allergies"""
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='allergies',
        verbose_name='بیمار'
    )
    
    allergen = models.CharField(
        max_length=255,
        verbose_name='آلرژن'
    )
    
    reaction = models.TextField(
        verbose_name='واکنش'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ('mild', 'خفیف'),
            ('moderate', 'متوسط'),
            ('severe', 'شدید'),
        ],
        default='mild',
        verbose_name='شدت'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    class Meta:
        db_table = 'allergies'
        verbose_name = 'آلرژی'
        verbose_name_plural = 'آلرژی‌ها'
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.allergen}"


class Medication(BaseModel):
    """Current medications being taken by patient"""
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medications',
        verbose_name='بیمار'
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name='نام دارو'
    )
    
    dosage = models.CharField(
        max_length=100,
        verbose_name='دوز'
    )
    
    frequency = models.CharField(
        max_length=100,
        verbose_name='فرکانس مصرف'
    )
    
    start_date = models.DateField(
        verbose_name='تاریخ شروع'
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاریخ پایان'
    )
    
    prescribed_by = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تجویز شده توسط'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        db_table = 'medications'
        verbose_name = 'دارو'
        verbose_name_plural = 'داروها'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.name}"
