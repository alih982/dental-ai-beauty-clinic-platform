"""
Doctor Domain Models
Medical specialties, doctor profiles, and working schedules
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.core.validators import PhoneNumberValidator, NationalCodeValidator


class Specialty(BaseModel):
    """Medical specialties"""
    
    name_fa = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='نام تخصص (فارسی)'
    )
    
    name_en = models.CharField(
        max_length=200,
        verbose_name='نام تخصص (انگلیسی)'
    )
    
    description_fa = models.TextField(
        blank=True,
        verbose_name='توضیحات (فارسی)'
    )

    description_en = models.TextField(
        blank=True,
        verbose_name='توضیحات (انگلیسی)'
    )
    
    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='آیکون'
    )
    
    class Meta:
        db_table = 'specialties'
        verbose_name = 'تخصص'
        verbose_name_plural = 'تخصص‌ها'
        ordering = ['name_fa']
    
    def __str__(self):
        return self.name_fa


class Doctor(BaseModel):
    """Doctor profiles with complete information"""
    
    # Link to User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctor_profile',
        verbose_name='حساب کاربری'
    )
    
    # Personal Information
    first_name_fa = models.CharField(
        max_length=100,
        verbose_name='نام (فارسی)'
    )

    first_name_en = models.CharField(
        max_length=100,
        verbose_name='نام (انگلیسی)'
    )
    
    last_name_fa = models.CharField(
        max_length=100,
        verbose_name='نام خانوادگی (فارسی)'
    )

    last_name_en = models.CharField(
        max_length=100,
        verbose_name='نام خانوادگی (انگلیسی)'
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
    
    # Professional Information
    medical_council_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره نظام پزشکی'
    )
    
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name='doctors',
        verbose_name='تخصص'
    )
    
    sub_specialty_fa = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='فوق تخصص (فارسی)'
    )

    sub_specialty_en = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='فوق تخصص (انگلیسی)'
    )
    
    years_of_experience = models.PositiveIntegerField(
        default=0,
        verbose_name='سال‌های تجربه'
    )
    
    education_fa = models.TextField(
        verbose_name='تحصیلات (فارسی)',
        blank=True
    )

    education_en = models.TextField(
        verbose_name='تحصیلات (انگلیسی)',
        blank=True
    )
    
    # Work Information
    clinic_name_fa = models.CharField(
        max_length=255,
        verbose_name='نام کلینیک/بیمارستان (فارسی)'
    )

    clinic_name_en = models.CharField(
        max_length=255,
        verbose_name='نام کلینیک/بیمارستان (انگلیسی)'
    )
    
    clinic_address_fa = models.TextField(
        verbose_name='آدرس (فارسی)'
    )

    clinic_address_en = models.TextField(
        verbose_name='آدرس (انگلیسی)'
    )
    
    city_fa = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='شهر (فارسی)'
    )

    city_en = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='شهر (انگلیسی)'
    )
    
    # Financial
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='هزینه ویزیت',
        help_text='به تومان'
    )
    
    accepts_insurance = models.BooleanField(
        default=False,
        verbose_name='پذیرش بیمه'
    )
    
    # Profile
    bio_fa = models.TextField(
        blank=True,
        verbose_name='بیوگرافی (فارسی)'
    )

    bio_en = models.TextField(
        blank=True,
        verbose_name='بیوگرافی (انگلیسی)'
    )
    
    profile_image = models.ImageField(
        upload_to='doctors/profiles/',
        blank=True,
        null=True,
        verbose_name='تصویر پروفایل'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='فعال'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تأیید شده'
    )
    
    # Statistics
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='امتیاز'
    )
    
    review_count = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد نظرات'
    )
    
    patient_count = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد بیماران'
    )
    
    class Meta:
        db_table = 'doctors'
        verbose_name = 'پزشک'
        verbose_name_plural = 'پزشکان'
        ordering = ['-rating', '-review_count']
        indexes = [
            models.Index(fields=['specialty', 'city_fa']),
            models.Index(fields=['specialty', 'city_en']),
            models.Index(fields=['is_active', 'is_verified']),
        ]
    
    def __str__(self):
        return self.get_full_name_fa()
    
    def get_full_name_fa(self):
        """Get doctor's full name in Persian"""
        return f"دکتر {self.first_name_fa} {self.last_name_fa}"

    def get_full_name_en(self):
        """Get doctor's full name in English"""
        return f"Dr. {self.first_name_en} {self.last_name_en}"
    
    def update_rating(self):
        """Update doctor rating based on reviews"""
        # TODO: Implement review system or remove this method
        # The reviews app doesn't exist yet - this is a placeholder
        pass


class DoctorWorkingHours(BaseModel):
    """Doctor working hours schedule"""
    
    class DayOfWeek(models.IntegerChoices):
        SATURDAY = 0, 'شنبه'
        SUNDAY = 1, 'یکشنبه'
        MONDAY = 2, 'دوشنبه'
        TUESDAY = 3, 'سه‌شنبه'
        WEDNESDAY = 4, 'چهارشنبه'
        THURSDAY = 5, 'پنجشنبه'
        FRIDAY = 6, 'جمعه'
    
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='working_hours',
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
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        db_table = 'doctor_working_hours'
        verbose_name = 'ساعت کاری پزشک'
        verbose_name_plural = 'ساعات کاری پزشکان'
        unique_together = [['doctor', 'day_of_week', 'start_time']]
    
    def __str__(self):
        return f"{self.doctor.get_full_name_fa()} - {self.get_day_of_week_display()}"
