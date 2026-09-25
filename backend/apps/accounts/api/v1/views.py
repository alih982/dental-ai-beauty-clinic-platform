from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .serializers import RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer, UserListSerializer

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class InitialUserView(generics.RetrieveAPIView):
    """Get current user info (Me)"""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


# ====================
# Admin User Management
# ====================
class UserListView(generics.ListAPIView):
    """
    Admin endpoint to list all users with filtering.
    Supports filtering by role (patient, doctor) and search.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = UserListSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_doctor', 'is_patient', 'is_active']
    search_fields = ['phone_number', 'first_name', 'last_name', 'email']
    ordering_fields = ['date_joined', 'last_login', 'first_name']
    ordering = ['-date_joined']


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin endpoint to get or update a specific user.
    Allows activating/deactivating users.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = UserListSerializer
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
