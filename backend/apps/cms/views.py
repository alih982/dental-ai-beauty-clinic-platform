from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import LandingPageHeader, MedicalService, PatientReview, AboutSection, NavMenuItem
from .serializers import (
    LandingPageHeaderSerializer, MedicalServiceSerializer, 
    PatientReviewSerializer, AboutSectionSerializer,
    NavMenuItemSerializer
)

# Cache timeout in seconds (15 minutes)
CACHE_TTL = 60 * 15

class CMSContentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Combined viewset to fetch all landing page content in one request
    """
    queryset = LandingPageHeader.objects.filter(is_active=True)
    serializer_class = LandingPageHeaderSerializer

    @action(detail=False, methods=['get'], url_path='landing-data')
    def landing_data(self, request):
        # Try to get from cache first
        cache_key = 'cms_landing_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        header = LandingPageHeader.objects.filter(is_active=True).first()
        services = MedicalService.objects.filter(is_active=True)
        reviews = PatientReview.objects.filter(is_active=True)
        about = AboutSection.objects.filter(is_active=True).first()
        menu = NavMenuItem.objects.filter(is_active=True, parent=None).order_by('order')

        response_data = {
            'header': LandingPageHeaderSerializer(header).data if header else None,
            'services': MedicalServiceSerializer(services, many=True).data,
            'reviews': PatientReviewSerializer(reviews, many=True).data,
            'about': AboutSectionSerializer(about).data if about else None,
            'menu': NavMenuItemSerializer(menu, many=True).data
        }
        
        # Cache the response
        cache.set(cache_key, response_data, CACHE_TTL)
        
        return Response(response_data)

class MedicalServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for medical services with caching
    """
    queryset = MedicalService.objects.filter(is_active=True)
    serializer_class = MedicalServiceSerializer
    pagination_class = None
    lookup_field = 'slug'

    def get_queryset(self):
        cache_key = 'medical_services_list'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return MedicalService.objects.filter(pk__in=[s.pk for s in cached_data])
        
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        cache_key = 'medical_services_list'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            serializer = self.get_serializer(cached_data, many=True)
            return Response(serializer.data)
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Cache for 15 minutes
        cache.set(cache_key, list(queryset), CACHE_TTL)
        
        return Response(serializer.data)

    @cache_page(CACHE_TTL)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class PatientReviewViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PatientReview.objects.filter(is_active=True)
    serializer_class = PatientReviewSerializer
    pagination_class = None

class NavMenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NavMenuItem.objects.filter(is_active=True, parent=None).order_by('order')
    serializer_class = NavMenuItemSerializer
    pagination_class = None
    
    def list(self, request, *args, **kwargs):
        cache_key = 'nav_menu_items'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            serializer = self.get_serializer(cached_data, many=True)
            return Response(serializer.data)
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        cache.set(cache_key, list(queryset), CACHE_TTL)
        
        return Response(serializer.data)
