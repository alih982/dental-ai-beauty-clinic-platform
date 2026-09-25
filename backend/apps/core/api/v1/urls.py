"""
Core API v1 URL Configuration
"""
from django.urls import path
from apps.core.api.v1 import views

urlpatterns = [
    path('system-settings/', views.system_settings, name='system-settings'),
    path('system-settings/public/', views.system_settings_public, name='system-settings-public'),
    path('system-health/', views.system_health, name='system-health'),
]
