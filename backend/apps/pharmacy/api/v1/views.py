"""
Pharmacy API Views - Fixed version with proper error handling
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

# Import models directly without re-export to avoid confusion
from apps.pharmacy.models import Cart, CartItem, Order, OrderItem
from apps.pharmacy.domain.models import Category, Medicine
from apps.prescriptions.models import Prescription

# Serializers
from .serializers import (
    CategorySerializer,
    MedicineSerializer,
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    OrderSerializer,
    CreateOrderSerializer,
    CheckoutSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing product categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in CategoryViewSet.list: {str(e)}")
            return Response(
                {'error': 'Failed to fetch categories', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in CategoryViewSet.retrieve: {str(e)}")
            return Response(
                {'error': 'Failed to fetch category', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MedicineViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing and searching medicines"""
    queryset = Medicine.objects.filter(is_active=True)
    serializer_class = MedicineSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_prescription_required']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in MedicineViewSet.list: {str(e)}")
            return Response(
                {'error': 'Failed to fetch medicines', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in MedicineViewSet.retrieve: {str(e)}")
            return Response(
                {'error': 'Failed to fetch medicine', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartViewSet(viewsets.ModelViewSet):
    """API for managing shopping cart"""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Cart.objects.none()
        if hasattr(user, 'patient_profile'):
            return Cart.objects.filter(
                patient=user.patient_profile,
                is_active=True
            ).prefetch_related('items', 'items__medicine')
        return Cart.objects.none()

    def get_patient(self):
        """Get patient from user"""
        if not self.request.user.is_authenticated:
            return None
        if hasattr(self.request.user, 'patient_profile'):
            return self.request.user.patient_profile
        # Try to get from Patient model
        from apps.patients.models import Patient
        try:
            return Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting patient: {str(e)}")
            return None

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get or create current cart for user"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            patient = self.get_patient()
            if not patient:
                return Response(
                    {'error': 'Patient profile not found. Please complete your profile in the dashboard first.', 'code': 'NO_PATIENT_PROFILE'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                cart, created = Cart.objects.get_or_create(
                    patient=patient,
                    is_active=True
                )
                # Prefetch items for better performance
                cart = Cart.objects.prefetch_related('items', 'items__medicine').get(id=cart.id)
            except Exception as e:
                logger.error(f"Error getting/creating cart: {str(e)}")
                return Response(
                    {'error': 'Failed to access cart', 'details': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in CartViewSet.current: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': 'Failed to get cart', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        # For demo/testing, allow requests without authentication check first
        # We'll handle auth inside the function
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required. Please login to add items to cart.', 'code': 'AUTH_REQUIRED'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        try:
            serializer = AddToCartSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Try to get patient from user
            patient = None
            try:
                patient = self.get_patient()
            except Exception as e:
                logger.error(f"Error getting patient: {str(e)}")
            
            if not patient:
                # For demo purposes, create a temporary response or return a clear message
                return Response(
                    {'error': 'Patient profile not found. Please complete your profile in the dashboard first.', 'code': 'NO_PATIENT_PROFILE'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get or create cart
            try:
                cart, _ = Cart.objects.get_or_create(
                    patient=patient,
                    is_active=True
                )
            except Exception as e:
                logger.error(f"Error getting/creating cart: {str(e)}")
                return Response(
                    {'error': 'Failed to access cart', 'details': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Get medicine - support both UUID and integer
            medicine_id = serializer.validated_data.get('medicine_id')
            
            if not medicine_id:
                return Response(
                    {'error': 'Medicine ID is required', 'code': 'MEDICINE_ID_REQUIRED'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Try to find medicine by UUID first, then by integer ID
            from apps.pharmacy.domain.models import Medicine
            
            medicine = None
            # Try UUID first
            try:
                medicine = Medicine.objects.get(
                    id=medicine_id,
                    is_active=True
                )
            except (Medicine.DoesNotExist, ValueError):
                # Try integer ID
                try:
                    int_id = int(medicine_id)
                    medicine = Medicine.objects.get(
                        id=int_id,
                        is_active=True
                    )
                except (ValueError, Medicine.DoesNotExist):
                    return Response(
                        {'error': f'Medicine not found with ID: {medicine_id}', 'code': 'MEDICINE_NOT_FOUND'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            if not medicine:
                return Response(
                    {'error': f'Medicine not found with ID: {medicine_id}', 'code': 'MEDICINE_NOT_FOUND'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check stock
            if medicine.stock < serializer.validated_data.get('quantity', 1):
                return Response(
                    {'error': f'Insufficient stock. Available: {medicine.stock}', 'code': 'INSUFFICIENT_STOCK'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check prescription requirement
            if medicine.is_prescription_required and not serializer.validated_data.get('prescription_id'):
                return Response(
                    {'error': 'Prescription required for this medicine', 'code': 'PRESCRIPTION_REQUIRED'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create cart item
            try:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    medicine=medicine,
                    defaults={
                        'quantity': serializer.validated_data.get('quantity', 1)
                    }
                )

                if not created:
                    # Update quantity
                    new_quantity = cart_item.quantity + serializer.validated_data.get('quantity', 1)
                    if medicine.stock < new_quantity:
                        return Response(
                            {'error': 'Insufficient stock for requested quantity', 'code': 'INSUFFICIENT_STOCK'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    cart_item.quantity = new_quantity
                    cart_item.save()
            except Exception as e:
                logger.error(f"Error creating/updating cart item: {str(e)}")
                return Response(
                    {'error': 'Failed to add item to cart', 'details': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Update prescription if provided
            prescription_id = serializer.validated_data.get('prescription_id')
            if prescription_id:
                from apps.prescriptions.models import Prescription
                try:
                    prescription = Prescription.objects.get(
                        id=prescription_id,
                        patient=patient
                    )
                    cart_item.prescription = prescription
                    cart_item.save()
                except Prescription.DoesNotExist:
                    pass
                except Exception as e:
                    logger.warning(f"Error linking prescription: {str(e)}")

            return Response(
                CartSerializer(cart).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in CartViewSet.add_item: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': 'Failed to add item to cart', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_add_prescription(self, request):
        """Add all medications from a prescription to the cart"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        prescription_id = request.data.get('prescription_id')
        if not prescription_id:
            return Response(
                {'error': 'Prescription ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        patient = self.get_patient()
        if not patient:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            prescription = Prescription.objects.get(id=prescription_id, patient=patient)
            
            # Get or create cart
            cart, _ = Cart.objects.get_or_create(patient=patient, is_active=True)
            
            added_items = []
            not_found_items = []
            
            # Iterate through medications in prescription
            # The medications field is a JSON list of objects/strings
            meds = prescription.medications if isinstance(prescription.medications, list) else []
            
            for med_data in meds:
                # Find matching medicine in pharmacy
                med_name = med_data.get('name') if isinstance(med_data, dict) else str(med_data)
                
                # Try simple name matching (fuzzy or exact)
                medicine = Medicine.objects.filter(
                    name__icontains=med_name,
                    is_active=True
                ).first()
                
                if medicine:
                    if medicine.stock > 0:
                        cart_item, created = CartItem.objects.get_or_create(
                            cart=cart,
                            medicine=medicine,
                            defaults={'quantity': 1}
                        )
                        cart_item.prescription = prescription
                        cart_item.save()
                        added_items.append(medicine.name)
                    else:
                        not_found_items.append(f"{med_name} (Out of stock)")
                else:
                    not_found_items.append(med_name)

            return Response({
                'status': 'success',
                'cart': CartSerializer(cart).data,
                'added_items': added_items,
                'not_found_items': not_found_items
            })
            
        except Prescription.DoesNotExist:
            return Response(
                {'error': 'Prescription not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in bulk_add_prescription: {str(e)}")
            return Response(
                {'error': 'Failed to process prescription', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """Update cart item quantity"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            item_id = request.data.get('item_id')
            quantity = request.data.get('quantity', 1)

            patient = self.get_patient()
            if not patient:
                return Response(
                    {'error': 'Patient profile not found', 'code': 'NO_PATIENT_PROFILE'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                cart_item = CartItem.objects.get(
                    id=item_id,
                    cart__patient=patient
                )
            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Item not found in cart', 'code': 'ITEM_NOT_FOUND'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check stock
            if cart_item.medicine.stock < quantity:
                return Response(
                    {'error': 'Insufficient stock', 'code': 'INSUFFICIENT_STOCK'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()

            cart = cart_item.cart
            return Response(CartSerializer(cart).data)
        except Exception as e:
            logger.error(f"Error in CartViewSet.update_item: {str(e)}")
            return Response(
                {'error': 'Failed to update cart item', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            item_id = request.data.get('item_id')
            patient = self.get_patient()
            
            if not patient:
                return Response(
                    {'error': 'Patient profile not found', 'code': 'NO_PATIENT_PROFILE'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                cart_item = CartItem.objects.get(
                    id=item_id,
                    cart__patient=patient
                )
                cart = cart_item.cart
                cart_item.delete()
                return Response(CartSerializer(cart).data)
            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Item not found in cart', 'code': 'ITEM_NOT_FOUND'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error in CartViewSet.remove_item: {str(e)}")
            return Response(
                {'error': 'Failed to remove cart item', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from cart"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            patient = self.get_patient()
            if patient:
                Cart.objects.filter(
                    patient=patient,
                    is_active=True
                ).delete()

            return Response({'status': 'Cart cleared'})
        except Exception as e:
            logger.error(f"Error in CartViewSet.clear: {str(e)}")
            return Response(
                {'error': 'Failed to clear cart', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderViewSet(viewsets.ModelViewSet):
    """API for managing orders"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Allow unauthenticated access for demo purposes on certain actions"""
        if self.action in ['my_orders']:
            return [permission() for permission in self.permission_classes]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient_profile'):
            return Order.objects.filter(
                patient=user.patient_profile
            ).prefetch_related('items').order_by('-created_at')
        elif user.is_staff or user.is_superuser:
            return Order.objects.all().prefetch_related('items').order_by('-created_at')
        return Order.objects.none()

    def get_patient(self):
        """Get patient from user"""
        if not self.request.user.is_authenticated:
            return None
        if hasattr(self.request.user, 'patient_profile'):
            return self.request.user.patient_profile
        from apps.patients.models import Patient
        try:
            return Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting patient: {str(e)}")
            return None

    def create(self, request, *args, **kwargs):
        try:
            serializer = CreateOrderSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            patient = self.get_patient()
            if not patient:
                return Response(
                    {'error': 'Patient profile not found', 'code': 'NO_PATIENT_PROFILE'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get active cart
            try:
                cart = Cart.objects.get(
                    patient=patient,
                    is_active=True
                ).prefetch_related('items', 'items__medicine')
            except Cart.DoesNotExist:
                return Response(
                    {'error': 'Cart is empty', 'code': 'EMPTY_CART'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not cart.items.exists():
                return Response(
                    {'error': 'Cart is empty', 'code': 'EMPTY_CART'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check prescription requirements
            for item in cart.items.all():
                if item.medicine.is_prescription_required and not item.prescription:
                    return Response(
                        {'error': f'Prescription required for {item.medicine.name}', 'code': 'PRESCRIPTION_REQUIRED'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create order
            order = Order.objects.create(
                patient=patient,
                delivery_address=serializer.validated_data['delivery_address'],
                delivery_phone=serializer.validated_data['delivery_phone'],
                delivery_name=serializer.validated_data['delivery_name'],
                notes=serializer.validated_data.get('notes', ''),
                subtotal=cart.get_total_price(),
                total=cart.get_total_price(),
            )

            # Link prescription if provided
            if serializer.validated_data.get('prescription_id'):
                from apps.prescriptions.models import Prescription
                try:
                    prescription = Prescription.objects.get(
                        id=serializer.validated_data['prescription_id'],
                        patient=patient
                    )
                    order.prescription = prescription
                    order.save()
                except Prescription.DoesNotExist:
                    pass

            # Create order items from cart items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    medicine=item.medicine,
                    medicine_name=item.medicine.name,
                    medicine_price=item.medicine.price,
                    quantity=item.quantity,
                )

                # Reduce stock
                item.medicine.stock -= item.quantity
                item.medicine.save()

            # Clear cart
            cart.items.all().delete()

            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error in OrderViewSet.create: {str(e)}")
            return Response(
                {'error': 'Failed to create order', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Complete checkout process"""
        try:
            serializer = CheckoutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            patient = self.get_patient()
            if not patient:
                return Response(
                    {'error': 'Patient profile not found', 'code': 'NO_PATIENT_PROFILE'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get active cart
            try:
                cart = Cart.objects.get(
                    patient=patient,
                    is_active=True
                ).prefetch_related('items', 'items__medicine')
            except Cart.DoesNotExist:
                return Response(
                    {'error': 'Cart is empty', 'code': 'EMPTY_CART'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not cart.items.exists():
                return Response(
                    {'error': 'Cart is empty', 'code': 'EMPTY_CART'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check prescription requirements
            for item in cart.items.all():
                if item.medicine.is_prescription_required and not item.prescription:
                    return Response(
                        {'error': f'Prescription required for {item.medicine.name}', 'code': 'PRESCRIPTION_REQUIRED'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create order with payment
            order = Order.objects.create(
                patient=patient,
                delivery_address=serializer.validated_data['delivery_address'],
                delivery_phone=serializer.validated_data['delivery_phone'],
                delivery_name=serializer.validated_data['delivery_name'],
                notes=serializer.validated_data.get('notes', ''),
                payment_method=serializer.validated_data.get('payment_method', 'online'),
                subtotal=cart.get_total_price(),
                total=cart.get_total_price(),
                status=Order.StatusChoices.CONFIRMED,
                payment_status=Order.PaymentStatusChoices.PENDING,
            )

            # Link prescription if provided
            if serializer.validated_data.get('prescription_id'):
                from apps.prescriptions.models import Prescription
                try:
                    prescription = Prescription.objects.get(
                        id=serializer.validated_data['prescription_id'],
                        patient=patient
                    )
                    order.prescription = prescription
                    order.save()
                except Prescription.DoesNotExist:
                    pass

            # Create order items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    medicine=item.medicine,
                    medicine_name=item.medicine.name,
                    medicine_price=item.medicine.price,
                    quantity=item.quantity,
                )

                # Reduce stock
                item.medicine.stock -= item.quantity
                item.medicine.save()

            # Clear cart
            cart.items.all().delete()

            return Response({
                'success': True,
                'order': OrderSerializer(order).data,
                'message': 'Order created successfully. Please complete payment.'
            })
        except Exception as e:
            logger.error(f"Error in OrderViewSet.checkout: {str(e)}")
            return Response(
                {'error': 'Failed to checkout', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        try:
            order = self.get_object()
            
            if order.status not in [Order.StatusChoices.PENDING, Order.StatusChoices.CONFIRMED]:
                return Response(
                    {'error': 'Order cannot be cancelled', 'code': 'CANNOT_CANCEL'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Restore stock
            for item in order.items.all():
                item.medicine.stock += item.quantity
                item.medicine.save()

            order.status = Order.StatusChoices.CANCELLED
            order.save()

            return Response(OrderSerializer(order).data)
        except Exception as e:
            logger.error(f"Error in OrderViewSet.cancel: {str(e)}")
            return Response(
                {'error': 'Failed to cancel order', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get current user's orders"""
        try:
            patient = self.get_patient()
            if not patient:
                return Response(
                    {'error': 'Patient profile not found', 'code': 'NO_PATIENT_PROFILE'},
                    status=status.HTTP_404_NOT_FOUND
                )

            orders = Order.objects.filter(
                patient=patient
            ).prefetch_related('items').order_by('-created_at')

            return Response(OrderSerializer(orders, many=True).data)
        except Exception as e:
            logger.error(f"Error in OrderViewSet.my_orders: {str(e)}")
            return Response(
                {'error': 'Failed to fetch orders', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
