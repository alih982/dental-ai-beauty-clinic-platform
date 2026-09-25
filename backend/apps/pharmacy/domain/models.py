from django.db import models
from apps.core.models import BaseModel


class Category(BaseModel):
    """Product categories for pharmacy"""
    
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='نام دسته‌بندی'
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='اسلاگ'
    )
    
    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='آیکون'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    class Meta:
        db_table = 'pharmacy_categories'
        verbose_name = 'دسته‌بندی دارو'
        verbose_name_plural = 'دسته‌بندی‌های دارو'
        ordering = ['name']

    def __str__(self):
        return self.name


class Medicine(BaseModel):
    """Medicine and health products"""
    
    name = models.CharField(
        max_length=255,
        verbose_name='نام دارو'
    )
    
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='اسلاگ'
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='medicines',
        verbose_name='دسته‌بندی'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    specifications = models.TextField(
        blank=True,
        verbose_name='مشخصات فنی'
    )
    
    image = models.ImageField(
        upload_to='pharmacy/medicines/',
        blank=True,
        null=True,
        verbose_name='تصویر محصول'
    )
    
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='قیمت',
        help_text='به تومان'
    )
    
    stock = models.IntegerField(
        default=0,
        verbose_name='موجودی در انبار'
    )
    
    pharmacy_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='نام داروخانه تامین‌کننده'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    is_prescription_required = models.BooleanField(
        default=False,
        verbose_name='نیاز به نسخه'
    )

    class Meta:
        db_table = 'pharmacy_medicines'
        verbose_name = 'دارو'
        verbose_name_plural = 'داروها'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
