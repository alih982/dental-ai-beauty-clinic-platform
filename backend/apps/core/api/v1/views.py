"""
System Settings API Views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

from apps.core.models import SystemSettings, ChatMode


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def system_settings(request):
    """
    Get or update system settings including chat mode.
    GET: Returns current system settings
    PUT: Updates system settings
    """
    settings = SystemSettings.get_settings()
    
    if request.method == 'GET':
        return Response({
            'chat_mode': settings.chat_mode,
            'chat_mode_display': settings.get_chat_mode_display(),
            'ai_provider': settings.ai_provider,
            'ai_model_name': settings.ai_model_name,
            'rag_enabled': settings.rag_enabled,
            'human_support_active': settings.human_support_active,
            'company_name': settings.company_name,
            'company_description': settings.company_description,
            'support_start_time': settings.support_start_time.strftime('%H:%M') if settings.support_start_time else None,
            'support_end_time': settings.support_end_time.strftime('%H:%M') if settings.support_end_time else None,
        })
    
    elif request.method == 'PUT':
        # Validate chat_mode if provided
        chat_mode = request.data.get('chat_mode')
        if chat_mode and chat_mode not in [mode[0] for mode in ChatMode.choices]:
            return Response(
                {'error': _('Invalid chat mode. Valid options: company_info, ai_response, human_support')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update fields
        if chat_mode:
            settings.chat_mode = chat_mode
        
        if 'ai_provider' in request.data:
            settings.ai_provider = request.data['ai_provider']
        
        if 'ai_model_name' in request.data:
            settings.ai_model_name = request.data['ai_model_name']
        
        if 'rag_enabled' in request.data:
            settings.rag_enabled = request.data['rag_enabled']
        
        if 'human_support_active' in request.data:
            settings.human_support_active = request.data['human_support_active']
        
        if 'company_name' in request.data:
            settings.company_name = request.data['company_name']
        
        if 'company_description' in request.data:
            settings.company_description = request.data['company_description']
        
        if 'support_start_time' in request.data:
            from datetime import time
            try:
                time_str = request.data['support_start_time']
                if time_str:
                    parts = time_str.split(':')
                    settings.support_start_time = time(int(parts[0]), int(parts[1]))
                else:
                    settings.support_start_time = None
            except (ValueError, IndexError):
                pass
        
        if 'support_end_time' in request.data:
            from datetime import time
            try:
                time_str = request.data['support_end_time']
                if time_str:
                    parts = time_str.split(':')
                    settings.support_end_time = time(int(parts[0]), int(parts[1]))
                else:
                    settings.support_end_time = None
            except (ValueError, IndexError):
                pass
        
        settings.save()
        
        return Response({
            'chat_mode': settings.chat_mode,
            'chat_mode_display': settings.get_chat_mode_display(),
            'ai_provider': settings.ai_provider,
            'ai_model_name': settings.ai_model_name,
            'rag_enabled': settings.rag_enabled,
            'human_support_active': settings.human_support_active,
            'company_name': settings.company_name,
            'company_description': settings.company_description,
            'support_start_time': settings.support_start_time.strftime('%H:%M') if settings.support_start_time else None,
            'support_end_time': settings.support_end_time.strftime('%H:%M') if settings.support_end_time else None,
        })


@api_view(['GET'])
@permission_classes([])  # No authentication required
def system_settings_public(request):
    """
    Public endpoint to get current chat mode - no auth required.
    Frontend can use this to get current chat mode for display.
    """
    settings = SystemSettings.get_settings()
    return Response({
        'chat_mode': settings.chat_mode,
        'chat_mode_display': settings.get_chat_mode_display(),
        'human_support_active': settings.human_support_active,
        'company_name': settings.company_name,
    })


@api_view(['GET'])
@permission_classes([])  # No authentication required for health check
def system_health(request):
    """
    Check health of various system components:
    - Database
    - Redis (Cache & Channel Layers)
    - Celery Workers
    """
    health = {
        'database': 'healthy',
        'redis': 'unknown',
        'celery': 'unknown',
        'workers': [],
    }
    
    # Check Redis
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health['redis'] = 'healthy'
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        health['redis'] = 'unhealthy'

    # Check Celery
    try:
        from config.celery import app as celery_app
        inspector = celery_app.control.inspect()
        active = inspector.active()
        if active:
            health['celery'] = 'healthy'
            health['workers'] = list(active.keys())
        else:
            health['celery'] = 'no_workers'
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        health['celery'] = 'unhealthy'

    return Response(health)
