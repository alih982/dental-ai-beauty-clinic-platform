"""Main URL configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.shortcuts import redirect
from django.http import JsonResponse

from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Define API version
API_VERSION = 'v1'

# Health check endpoint
def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'hospital_backend'})

urlpatterns = [
    # Health check endpoint (no auth required)
    path('health/', health_check, name='health_check'),
    
    # API Documentation (usually not translated)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# API URLs without i18n prefix (for mobile apps and frontend)
urlpatterns += [
    # Pharmacy API - no language prefix
    path('api/pharmacy/', include(f'apps.pharmacy.api.{API_VERSION}.urls')),
    path('api/prescriptions/', include(f'apps.prescriptions.api.{API_VERSION}.urls')),
    path('api/chat/', include(f'apps.chat.api.{API_VERSION}.urls')),
    path('api/appointments/', include(f'apps.appointments.api.{API_VERSION}.urls')),
    path('api/notifications/', include(f'apps.notifications.api.{API_VERSION}.urls')),

    path('api/accounts/', include(f'apps.accounts.api.{API_VERSION}.urls')),
    path('api/core/', include(f'apps.core.api.{API_VERSION}.urls')),
    
    # Dashboard API - for admin/doctor dashboards
    path('api/dashboard/', include('apps.dashboard.urls')),
]

urlpatterns += i18n_patterns(
    # Admin
    path('admin/', admin.site.urls),
    
    # Pharmacy & Other apps - with language prefix
    path('appointments/', include(f'apps.appointments.api.{API_VERSION}.urls')),
    path('doctors/', include(f'apps.doctors.api.{API_VERSION}.urls')),
    path('patients/', include(f'apps.patients.api.{API_VERSION}.urls')),
    path('pharmacy/', include(f'apps.pharmacy.api.{API_VERSION}.urls')),
    path('chat/', include(f'apps.chat.api.{API_VERSION}.urls')),
    path('prescriptions/', include(f'apps.prescriptions.api.{API_VERSION}.urls')),
    path('cms/', include('apps.cms.urls')),
    path('reports/', include('apps.reports.urls')),
    path('accounts/', include(f'apps.accounts.api.{API_VERSION}.urls')),
    path('core/', include(f'apps.core.api.{API_VERSION}.urls')),
    
    # Auth & Dashboard
    path('auth/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    
    # Home URL
    path('', include('apps.dashboard.urls')),
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

