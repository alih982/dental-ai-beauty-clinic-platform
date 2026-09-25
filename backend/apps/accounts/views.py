from django.shortcuts import redirect
from django.views import View
from django.contrib.auth import logout
from django.http import JsonResponse
from config.dynamic_settings import settings

# API-First Backend - No HTML templates, redirect to frontend

def api_login_success(request):
    """API endpoint for login success - frontend calls this after JWT"""
    return JsonResponse({'status': 'success', 'redirect': f'{settings.FRONTEND_URL}/dashboard'})

def logout_view(request):
    """API logout + redirect"""
    logout(request)
    return redirect(f'{settings.FRONTEND_URL}/login')

class HealthCheckView(View):
    """API health check"""
    def get(self, request):
        return JsonResponse({'status': 'ok', 'service': 'auth-api'})

