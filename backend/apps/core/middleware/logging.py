"""
Request/Response Logging Middleware
Tracks API requests for monitoring and debugging
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve

logger = logging.getLogger('api')
monitoring_logger = logging.getLogger('monitoring')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all HTTP requests and responses.
    Useful for monitoring, debugging, and security auditing.
    """
    
    def process_request(self, request):
        """Log incoming request"""
        request._start_time = time.time()
        
        # Log request details
        logger.info(
            f"REQUEST {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
        
        return None
    
    def process_response(self, request, response):
        """Log response details"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Determine log level based on status code
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            
            # Log response
            logger.log(
                log_level,
                f"RESPONSE {request.method} {request.path} {response.status_code} ({duration:.3f}s)",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                    'ip': self.get_client_ip(request),
                }
            )
            
            # Structured logging for monitoring
            monitoring_logger.info(
                "API Request",
                extra={
                    'event': 'api_request',
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': int(duration * 1000),
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'ip': self.get_client_ip(request),
                }
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions"""
        logger.error(
            f"EXCEPTION {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'method': request.method,
                'path': request.path,
                'exception': str(exception),
                'exception_type': type(exception).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': self.get_client_ip(request),
            }
        )
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DatabaseQueryLoggingMiddleware(MiddlewareMixin):
    """
    Log database query performance.
    Only enable in development or staging.
    """
    
    def process_request(self, request):
        """Reset query counter"""
        from django.db import connection
        connection.queries_log.clear()
        return None
    
    def process_response(self, request, response):
        """Log query statistics"""
        from django.db import connection
        
        if len(connection.queries) > 0:
            total_time = sum(float(q['time']) for q in connection.queries)
            
            logger.debug(
                f"DB Queries: {len(connection.queries)} queries in {total_time:.3f}s",
                extra={
                    'path': request.path,
                    'query_count': len(connection.queries),
                    'total_time': total_time,
                }
            )
            
            # Warn about slow queries
            slow_queries = [q for q in connection.queries if float(q['time']) > 0.1]
            if slow_queries:
                logger.warning(
                    f"Slow queries detected: {len(slow_queries)} queries > 100ms",
                    extra={
                        'path': request.path,
                        'slow_query_count': len(slow_queries),
                    }
                )
        
        return response
