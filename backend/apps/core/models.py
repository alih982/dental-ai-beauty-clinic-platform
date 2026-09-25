"""
Base Models Module - Abstract base classes for all models

Provides:
- Soft delete functionality
- Automatic timestamps
- UUID primary keys for distributed systems
- Async-compatible query methods
"""
import uuid
from django.db import models
from django.utils import timezone
from asgiref.sync import sync_to_async


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet with soft delete support"""
    
    def delete(self):
        """Soft delete all objects in queryset"""
        return super().update(deleted_at=timezone.now(), is_deleted=True)
    
    def hard_delete(self):
        """Permanently delete all objects"""
        return super().delete()
    
    def alive(self):
        """Return only non-deleted objects"""
        return self.filter(is_deleted=False)
    
    def dead(self):
        """Return only deleted objects"""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager with soft delete support"""
    
    def get_queryset(self):
        """Return only alive objects by default"""
        return SoftDeleteQuerySet(self.model, using=self._db).alive()
    
    def all_with_deleted(self):
        """Return all objects including deleted"""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def deleted_only(self):
        """Return only deleted objects"""
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class BaseModel(models.Model):
    """
    Abstract base model with common fields and functionality.
    
    Features:
    - UUID primary key for distributed systems
    - Automatic created_at/updated_at timestamps
    - Soft delete support
    - Async query helpers
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شناسه یکتا'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد',
        db_index=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین تغییر'
    )
    
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='حذف شده',
        db_index=True
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ حذف'
    )
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Access all objects including deleted
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete the object"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object"""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore a soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    
    # Async helpers for performance
    @classmethod
    async def aget_or_none(cls, **kwargs):
        """Async get object or return None"""
        try:
            return await cls.objects.aget(**kwargs)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    async def alist(cls, **filters):
        """Async list all objects matching filters"""
        queryset = cls.objects.filter(**filters) if filters else cls.objects.all()
        return await sync_to_async(list)(queryset)
    
    @classmethod
    async def acount(cls, **filters):
        """Async count objects"""
        queryset = cls.objects.filter(**filters) if filters else cls.objects.all()
        return await queryset.acount()
    
    async def arefresh_from_db(self):
        """Async refresh from database"""
        await sync_to_async(self.refresh_from_db)()
    
    async def asave(self, *args, **kwargs):
        """Async save"""
        await sync_to_async(self.save)(*args, **kwargs)
    
    async def adelete(self):
        """Async soft delete"""
        await sync_to_async(self.delete)()


class TimeStampedModel(models.Model):
    """
    Simple timestamped model without soft delete.
    Use when you don't need soft delete functionality.
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین تغییر'
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class ChatMode(models.TextChoices):
    """Chat mode choices for the system"""
    RAG = 'rag', 'سیستم RAG (اطلاعات تخصصی)'
    FINE_TUNED = 'fine_tuned', 'هوش مصنوعی Fine-tune شده'
    HUMAN_SUPPORT = 'human_support', 'پشتیبانی انسانی'


class SystemSettings(models.Model):
    """
    Global system settings for the hospital application.
    Stores configuration like chat mode, AI settings, etc.
    """
    
    # Chat Configuration
    chat_mode = models.CharField(
        max_length=20,
        choices=ChatMode.choices,
        default=ChatMode.RAG,
        verbose_name='نوع پاسخگویی چت'
    )
    
    # AI Configuration
    ai_provider = models.CharField(
        max_length=50,
        default='mock',
        verbose_name='ارائه‌دهنده هوش مصنوعی'
    )
    
    ai_model_name = models.CharField(
        max_length=100,
        default='gemma',
        verbose_name='نام مدل هوش مصنوعی'
    )
    
    rag_enabled = models.BooleanField(
        default=True,
        verbose_name='فعال بودن حالت RAG'
    )
    
    # Human Support Configuration
    default_support_doctor_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='پزشک پشتیبان پیش‌فرض'
    )
    
    support_notification_email = models.EmailField(
        blank=True,
        verbose_name='ایمیل اطلاع‌رسانی پشتیبانی'
    )
    
    # System Info
    company_name = models.CharField(
        max_length=200,
        default='DoctorHub',
        verbose_name='نام شرکت'
    )
    
    company_description = models.TextField(
        blank=True,
        verbose_name='توضیحات شرکت'
    )
    
    # Active Hours
    human_support_active = models.BooleanField(
        default=True,
        verbose_name='پشتیبانی انسانی فعال'
    )
    
    support_start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='شروع ساعات پشتیبانی'
    )
    
    support_end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='پایان ساعات پشتیبانی'
    )
    
    # Timestamps
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین به‌روزرسانی'
    )
    
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_settings_updates',
        verbose_name='به‌روزرسانی توسط'
    )
    
    class Meta:
        verbose_name = 'تنظیمات سیستم'
        verbose_name_plural = 'تنظیمات سیستم'
    
    def __str__(self):
        return f"تنظیمات سیستم - {self.get_chat_mode_display()}"
    
    @classmethod
    def get_settings(cls):
        """Get or create system settings singleton"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'chat_mode': ChatMode.RAG,
                'ai_provider': 'mock',
                'ai_model_name': 'gemma',
                'rag_enabled': True,
                'human_support_active': True,
                'company_name': 'DoctorHub',
            }
        )
        return settings
    
    def is_human_support_available(self):
        """Check if human support is currently available"""
        if not self.human_support_active:
            return False
        
        if not self.support_start_time or not self.support_end_time:
            return True  # 24/7 support
        
        from django.utils import timezone
        now = timezone.now().time()
        return self.support_start_time <= now <= self.support_end_time
