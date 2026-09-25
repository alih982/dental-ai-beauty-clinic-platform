"""
Logging utilities for structured logging
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict
import traceback


class StructuredLogger:
    """
    Wrapper for structured logging with additional context.
    Useful for monitoring and log aggregation systems (ELK, Splunk, etc.)
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log_structured(self, level: int, message: str, **kwargs):
        """Log with structured data"""
        extra_data = {
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        self.logger.log(level, message, extra=extra_data)
    
    def info(self, message: str, **kwargs):
        """Log info with structured data"""
        self._log_structured(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning with structured data"""
        self._log_structured(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Log error with optional exception"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['exception_type'] = type(exception).__name__
            kwargs['traceback'] = traceback.format_exc()
        
        self._log_structured(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug with structured data"""
        self._log_structured(logging.DEBUG, message, **kwargs)


def log_database_operation(operation: str, model: str, duration: float, **kwargs):
    """
    Log database operations for monitoring.
    
    Args:
        operation: Operation type (create, update, delete, select)
        model: Model name
        duration: Operation duration in seconds
        **kwargs: Additional context
    """
    logger = logging.getLogger('monitoring')
    logger.info(
        f"DB Operation: {operation} {model}",
        extra={
            'event': 'db_operation',
            'operation': operation,
            'model': model,
            'duration_ms': int(duration * 1000),
            **kwargs
        }
    )


def log_api_call(endpoint: str, method: str, status_code: int, duration: float, **kwargs):
    """
    Log API calls for monitoring.
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration: Request duration in seconds
        **kwargs: Additional context
    """
    logger = logging.getLogger('monitoring')
    logger.info(
        f"API Call: {method} {endpoint} - {status_code}",
        extra={
            'event': 'api_call',
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': int(duration * 1000),
            **kwargs
        }
    )


def log_business_event(event_type: str, event_data: Dict[str, Any]):
    """
    Log business events for analytics.
    
    Examples:
        - appointment.booked
        - payment.completed
        - user.registered
    
    Args:
        event_type: Type of event
        event_data: Event data
    """
    logger = logging.getLogger('monitoring')
    logger.info(
        f"Business Event: {event_type}",
        extra={
            'event': 'business_event',
            'event_type': event_type,
            'event_data': event_data,
        }
    )


def log_security_event(event_type: str, user: str = None, ip: str = None, **kwargs):
    """
    Log security-related events.
    
    Args:
        event_type: Security event type (login, logout, failed_login, etc.)
        user: Username
        ip: IP address
        **kwargs: Additional context
    """
    logger = logging.getLogger('django.security')
    logger.warning(
        f"Security Event: {event_type}",
        extra={
            'event': 'security_event',
            'event_type': event_type,
            'user': user,
            'ip': ip,
            **kwargs
        }
    )


class DatabaseQueryLogger:
    """
    Context manager for logging database query performance.
    
    Usage:
        with DatabaseQueryLogger('get_appointments'):
            appointments = Appointment.objects.filter(...)
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        from django.db import connection
        self.start_time = datetime.now()
        self.initial_queries = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        from django.db import connection
        
        duration = (datetime.now() - self.start_time).total_seconds()
        query_count = len(connection.queries) - self.initial_queries
        
        logger = logging.getLogger('apps')
        logger.debug(
            f"DB Operation '{self.operation_name}': {query_count} queries in {duration:.3f}s",
            extra={
                'operation': self.operation_name,
                'query_count': query_count,
                'duration': duration,
            }
        )
        
        return False
