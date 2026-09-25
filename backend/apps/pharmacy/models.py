from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.patients.models import PatientProfile as Patient
from apps.prescriptions.models import Prescription
import uuid


class Cart(BaseModel):
    """Shopping cart for pharmacy items"""
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='بیمار'
    )
    
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name='کلید جلسه'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    class Meta:
        db_table = 'pharmacy_carts'
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart {self.id} - {self.patient}"

    def get_total_price(self):
        """Calculate total price of all items in cart"""
        total = sum(item.get_total_price() for item in self.items.all())
        return total

    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())


class CartItem(BaseModel):
    """Individual item in a shopping cart"""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سبد خرید'
    )
    
    medicine = models.ForeignKey(
        'pharmacy.Medicine',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='دارو'
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='تعداد'
    )
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items',
        verbose_name='نسخه مرتبط'
    )

    class Meta:
        db_table = 'pharmacy_cart_items'
        verbose_name = 'آیتم سبد خرید'
        verbose_name_plural = 'آیتم‌های سبد خرید'
        unique_together = ['cart', 'medicine']

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"

    def get_total_price(self):
        """Calculate total price for this item"""
        return self.medicine.price * self.quantity


class Order(BaseModel):
    """Order for pharmacy items"""
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'در انتظار'
        CONFIRMED = 'confirmed', 'تأیید شده'
        PROCESSING = 'processing', 'در حال پردازش'
        SHIPPED = 'shipped', 'ارسال شده'
        DELIVERED = 'delivered', 'تحویل داده شده'
        CANCELLED = 'cancelled', 'لغو شده'
    
    class PaymentStatusChoices(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        PAID = 'paid', 'پرداخت شده'
        FAILED = 'failed', 'ناموفق'
        REFUNDED = 'refunded', 'بازگشت داده شده'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شماره سفارش'
    )
    
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره سفارش'
    )
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='pharmacy_orders',
        verbose_name='بیمار'
    )
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='نسخه'
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name='وضعیت'
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
        verbose_name='وضعیت پرداخت'
    )
    
    # Delivery Information
    delivery_address = models.TextField(
        verbose_name='آدرس تحویل'
    )
    
    delivery_phone = models.CharField(
        max_length=20,
        verbose_name='شماره تماس تحویل'
    )
    
    delivery_name = models.CharField(
        max_length=200,
        verbose_name='نام تحویل‌گیرنده'
    )
    
    # Pricing
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='جمع Parts'
    )
    
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='تخفیف'
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مجموع'
    )
    
    # Payment Information
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='روش پرداخت'
    )
    
    payment_reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='شماره پیگیری پرداخت'
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )

    class Meta:
        db_table = 'pharmacy_orders'
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: ORD-YYYYMMDD-XXXX
            from django.utils import timezone
            today = timezone.now().date()
            last_order = Order.objects.filter(
                created_at__date=today
            ).order_by('-created_at').first()
            
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.order_number = f"ORD-{today.strftime('%Y%m%d')}-{new_num:04d}"
        
        super().save(*args, **kwargs)

    def calculate_total(self):
        """Calculate order total from items"""
        self.subtotal = sum(item.get_total_price() for item in self.items.all())
        self.total = self.subtotal - self.discount
        return self.total


class OrderItem(BaseModel):
    """Individual item in an order"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سفارش'
    )
    
    medicine = models.ForeignKey(
        'pharmacy.Medicine',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='دارو'
    )
    
    medicine_name = models.CharField(
        max_length=255,
        verbose_name='نام دارو'
    )
    
    medicine_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='قیمت واحد'
    )
    
    quantity = models.PositiveIntegerField(
        verbose_name='تعداد'
    )
    
    prescription_item = models.JSONField(
        null=True,
        blank=True,
        verbose_name='آیتم نسخه'
    )

    class Meta:
        db_table = 'pharmacy_order_items'
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return f"{self.medicine_name} x {self.quantity}"

    def get_total_price(self):
        """Calculate total price for this item"""
        return self.medicine_price * self.quantity



# Re-export from domain for Django app registry
from apps.pharmacy.domain.models import Category, Medicine

__all__ = ['Cart', 'CartItem', 'Order', 'OrderItem', 'Category', 'Medicine']

