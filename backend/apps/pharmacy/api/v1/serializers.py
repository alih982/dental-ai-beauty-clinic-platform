from rest_framework import serializers
from apps.pharmacy.models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_price = serializers.DecimalField(
        source='medicine.price',
        max_digits=12,
        decimal_places=0,
        read_only=True
    )
    medicine_image = serializers.ImageField(source='medicine.image', read_only=True)
    total_price = serializers.SerializerMethodField()
    requires_prescription = serializers.BooleanField(
        source='medicine.is_prescription_required',
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'medicine',
            'medicine_name',
            'medicine_price',
            'medicine_image',
            'quantity',
            'total_price',
            'requires_prescription',
            'prescription',
        ]
        read_only_fields = ['id']

    def get_total_price(self, obj):
        return obj.get_total_price()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'patient',
            'items',
            'total_price',
            'total_items',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_total_items(self, obj):
        return obj.get_total_items()


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart - accepts both UUID and integer"""
    medicine_id = serializers.CharField()  # Changed to CharField to accept both UUID and integer
    quantity = serializers.IntegerField(min_value=1, default=1)
    prescription_id = serializers.UUIDField(required=False, allow_null=True)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'medicine_name',
            'medicine_price',
            'quantity',
            'prescription_item',
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'patient',
            'patient_name',
            'prescription',
            'status',
            'status_display',
            'payment_status',
            'payment_status_display',
            'delivery_address',
            'delivery_phone',
            'delivery_name',
            'subtotal',
            'discount',
            'total',
            'payment_method',
            'payment_reference',
            'notes',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'order_number',
            'subtotal',
            'discount',
            'total',
            'created_at',
            'updated_at',
        ]


class CreateOrderSerializer(serializers.Serializer):
    delivery_address = serializers.CharField()
    delivery_phone = serializers.CharField(max_length=20)
    delivery_name = serializers.CharField(max_length=200)
    notes = serializers.CharField(required=False, allow_blank=True)
    prescription_id = serializers.UUIDField(required=False, allow_null=True)


class CheckoutSerializer(serializers.Serializer):
    delivery_address = serializers.CharField()
    delivery_phone = serializers.CharField(max_length=20)
    delivery_name = serializers.CharField(max_length=200)
    notes = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(default='online')
    prescription_id = serializers.UUIDField(required=False, allow_null=True)



# Domain serializers
from apps.pharmacy.domain.models import Category, Medicine


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'slug', 'category', 'category_name', 'description',
            'specifications', 'image', 'price', 'stock', 'pharmacy_name',
            'is_active', 'is_prescription_required', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
