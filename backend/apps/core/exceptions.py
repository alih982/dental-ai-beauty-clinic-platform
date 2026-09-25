"""Custom exception handlers for DRF"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    Provides consistent error response format.
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response format
        custom_response_data = {
            'success': False,
            'error': {
                'message': 'خطایی رخ داده است',
                'details': response.data
            }
        }
        response.data = custom_response_data
        return response
    
    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                'success': False,
                'error': {
                    'message': 'خطای اعتبارسنجی',
                    'details': exc.messages if hasattr(exc, 'messages') else str(exc)
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle unexpected errors
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return Response(
        {
            'success': False,
            'error': {
                'message': 'خطای سیستمی',
                'details': str(exc)
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
