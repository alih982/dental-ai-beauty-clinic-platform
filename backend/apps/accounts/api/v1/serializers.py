from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User Profile"""
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'first_name', 'last_name', 'email', 'is_doctor', 'is_patient')
        read_only_fields = ('is_doctor', 'is_patient')

class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for User listing in Admin Dashboard.
    Includes role field and additional user info.
    """
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'phone_number', 'first_name', 'last_name', 'email',
            'is_doctor', 'is_patient', 'is_active', 'is_superuser',
            'date_joined', 'last_login', 'role'
        )
        read_only_fields = ('date_joined', 'last_login', 'is_superuser')
    
    def get_role(self, obj):
        if obj.is_superuser:
            return 'admin'
        elif obj.is_doctor:
            return 'doctor'
        elif obj.is_patient:
            return 'patient'
        return 'user'

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for User Registration"""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('phone_number', 'password', 'first_name', 'last_name', 'email', 'is_doctor', 'is_patient')
    
    def validate(self, attrs):
        if not attrs.get('is_doctor') and not attrs.get('is_patient'):
            raise serializers.ValidationError("Must register as either a doctor or a patient.")
        if attrs.get('is_doctor') and attrs.get('is_patient'):
            raise serializers.ValidationError("Cannot register as both a doctor and a patient.")
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            is_doctor=validated_data.get('is_doctor', False),
            is_patient=validated_data.get('is_patient', False)
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT Token Serializer to include user info"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['phone_number'] = user.phone_number
        token['is_doctor'] = user.is_doctor
        token['is_patient'] = user.is_patient
        token['is_superuser'] = user.is_superuser
        
        return token
