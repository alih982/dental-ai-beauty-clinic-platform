from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
# from rest_framework.exceptions import Http404
from django.http import Http404
from asgiref.sync import async_to_sync
from django_filters.rest_framework import DjangoFilterBackend

from apps.doctors.domain.models import Specialty, Doctor
from apps.doctors.domain.services import DoctorService, SpecialtyService
from apps.doctors.api.v1.serializers import (
    DoctorListSerializer, 
    DoctorDetailSerializer, 
    SpecialtySerializer
)

class SpecialtyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Specialty.objects.filter(is_deleted=False)
    serializer_class = SpecialtySerializer
    permission_classes = [AllowAny]


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name_fa', 'last_name_fa', 'first_name_en', 'last_name_en', 'bio_fa', 'bio_en']
    ordering_fields = ['rating', 'years_of_experience', 'fee']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = DoctorService()

    def get_queryset(self):
        """Standard queryset for doctors - only verified for list view"""
        return Doctor.objects.filter(is_active=True, is_verified=True).select_related('specialty')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DoctorDetailSerializer
        return DoctorListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to allow viewing individual doctor profiles
        even if not verified (for public doctor profile pages)
        """
        # Get the doctor by ID regardless of verification status
        try:
            # First try with the default queryset (verified only)
            instance = self.get_object()
        except Http404:
            # If not found, try with all active doctors (including unverified)
            try:
                instance = Doctor.objects.select_related('specialty').get(
                    pk=kwargs.get('pk'),
                    is_active=True
                )
            except Doctor.DoesNotExist:
                raise Http404("Doctor not found")
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """List doctors with advanced filtering"""
        specialty_id = request.query_params.get('specialty_id')
        city = request.query_params.get('city')
        query = request.query_params.get('search')
        
        # Use service for complex filtering if needed, 
        # but for list we can use standard DRF filtering
        queryset = self.filter_queryset(self.get_queryset())
        
        if specialty_id and specialty_id != 'all':
            queryset = queryset.filter(specialty_id=specialty_id)
        
        if city:
            queryset = queryset.filter(city_fa__icontains=city) | queryset.filter(city_en__icontains=city)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='top-rated')
    def top_rated(self, request):
        """Get top rated doctors using service layer"""
        limit = int(request.query_params.get('limit', 10))
        doctors = async_to_sync(self.service.get_top_rated_doctors)(limit=limit)
        serializer = DoctorListSerializer(doctors, many=True, context={'request': request})
        return Response(serializer.data)
