"""
Centralized Dynamic Celery Configuration for Smart Health Platform

This module provides a SINGLE SOURCE OF TRUTH for ALL Celery configurations.
All settings can be changed via environment variables - no code changes needed!

Usage:
    from config.celery_config import celery_config
    
    # Access any Celery configuration
    broker_url = celery_config['broker_url']
    result_backend = celery_config['result_backend']
    
    # Or use the get_celery_config() function for dynamic updates
    config = get_celery_config()
"""

from config.dynamic_settings import settings as dyn_settings
from typing import Dict, Any, Optional
from functools import lru_cache


class CeleryConfig:
    """
    Dynamic Celery Configuration Class.
    All values are read from environment variables via dynamic_settings.
    """
    
    def __init__(self):
        # Core settings from dynamic_settings - Using computed URLs for proper DB isolation
        self._broker_url = dyn_settings.celery_broker_url
        self._result_backend = dyn_settings.celery_result_backend_url
        self._task_serializer = dyn_settings.CELERY_TASK_SERIALIZER
        self._result_serializer = dyn_settings.CELERY_RESULT_SERIALIZER
        self._accept_content = dyn_settings.CELERY_ACCEPT_CONTENT
        self._timezone = dyn_settings.CELERY_TIMEZONE
        self._enable_utc = dyn_settings.CELERY_ENABLE_UTC
        self._task_track_started = dyn_settings.CELERY_TASK_TRACK_STARTED
        self._task_time_limit = dyn_settings.CELERY_TASK_TIME_LIMIT
        self._task_soft_time_limit = dyn_settings.CELERY_TASK_TIME_LIMIT + 300  # Soft limit = hard limit + 5 min
        self._worker_prefetch_multiplier = dyn_settings.CELERY_WORKER_PREFETCH_MULTIPLIER
        self._worker_max_tasks_per_child = dyn_settings.CELERY_WORKER_MAX_TASKS_PER_CHILD
        self._task_acks_late = dyn_settings.CELERY_TASK_ACKS_LATE
        self._beat_scheduler = dyn_settings.CELERYBEAT_SCHEDULER
        
        # Task routes for better organization
        self._task_routes = self._get_task_routes()
        
        # Task annotations for monitoring
        self._task_annotations = self._get_task_annotations()
        
        # Result expires
        self._result_expires = 60 * 60 * 24 * 7  # 7 days
        
        # Task compression
        self._task_compression = 'gzip'
        
        # Result compression
        self._result_compression = 'gzip'
        
        # Worker settings
        self._worker_disable_rate_limits = False
        self._worker_send_task_events = True
        self._task_send_sent_event = True
        
        # Broker settings
        self._broker_connection_retry = True
        self._broker_connection_retry_on_startup = True
        self._broker_connection_max_retries = 10
        
        # Redis broker settings
        self._broker_pool_limit = 10
        self._redis_max_connections = 50
        self._redis_socket_timeout = 5
        self._redis_socket_connect_timeout = 5
        
        # Monitoring
        self._worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
        self._worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
        self._task_log_format = '[%(asctime)s: %(levelname)s][%(task_name)s(%(task_id)s)] %(message)s'
        
        # Email notifications for task failures
        self._task_ignore_result = False
        self._task_store_errors_even_if_ignored = True
        
        # Time limits
        self._task_acks_late = True
        self._task_reject_on_worker_lost = True
        
        # Retry settings
        self._task_default_retry_delay = 180  # 3 minutes
        self._task_max_retries = 3
        
        # Rate limiting
        self._task_default_rate_limit = '100/m'
        
        # Priority settings
        self._task_inherit_parent_priority = True
        self._worker_prefetch_multiplier = 4
        
        # JSON serialization settings
        self._task_serializer = 'json'
        self._result_serializer = 'json'
        self._accept_content = ['json']
        
        # MongoDB-like result backend settings (using Redis)
        self._result_extended = True
        
        # Celery Beat settings
        self._beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
        self._beat_sync_every = 3
        
        # Security
        self._task_always_eager = dyn_settings.DEBUG  # Eager mode for development
        
        # Import tasks
        self._imports = (
            'apps.notifications.tasks',
            'apps.appointments.tasks',
            'apps.chat.tasks',
            'apps.prescriptions.tasks',
            'apps.core.tasks',
        )
        
        # Include modules
        self._include = (
            'apps.notifications.tasks',
            'apps.appointments.tasks',
            'apps.chat.tasks',
            'apps.prescriptions.tasks',
            'apps.core.tasks',
        )
    
    def _get_task_routes(self) -> Dict[str, Dict[str, str]]:
        """Define task routes for better organization"""
        return {
            # Notifications - high priority
            'apps.notifications.tasks.send_live_notification': {'queue': 'notifications', 'routing_key': 'notification.send'},
            'apps.notifications.tasks.send_email_notification_task': {'queue': 'notifications', 'routing_key': 'notification.email'},
            
            # Appointments - high priority
            'apps.appointments.tasks.*': {'queue': 'appointments', 'routing_key': 'appointment.*'},
            
            # Chat - high priority
            'apps.chat.tasks.*': {'queue': 'chat', 'routing_key': 'chat.*'},
            
            # Prescriptions - medium priority
            'apps.prescriptions.tasks.*': {'queue': 'prescriptions', 'routing_key': 'prescription.*'},
            
            # Core tasks - low priority
            'apps.core.tasks.*': {'queue': 'default', 'routing_key': 'default'},
        }
    
    def _get_task_annotations(self) -> Dict[str, Dict[str, Any]]:
        """Define task annotations for monitoring"""
        return {
            '*': {
                'rate_limit': '100/m',
                'acks_late': True,
            },
            'apps.notifications.tasks.send_live_notification': {
                'rate_limit': '200/m',
                'time_limit': 30,
            },
            'apps.notifications.tasks.send_email_notification_task': {
                'rate_limit': '50/m',
                'time_limit': 60,
            },
        }
    
    @property
    def broker_url(self) -> str:
        return self._broker_url
    
    @property
    def result_backend(self) -> str:
        return self._result_backend
    
    @property
    def task_serializer(self) -> str:
        return self._task_serializer
    
    @property
    def result_serializer(self) -> str:
        return self._result_serializer
    
    @property
    def accept_content(self) -> list:
        return self._accept_content
    
    @property
    def timezone(self) -> str:
        return self._timezone
    
    @property
    def enable_utc(self) -> bool:
        return self._enable_utc
    
    @property
    def task_track_started(self) -> bool:
        return self._task_track_started
    
    @property
    def task_time_limit(self) -> int:
        return self._task_time_limit
    
    @property
    def task_soft_time_limit(self) -> int:
        return self._task_soft_time_limit
    
    @property
    def worker_prefetch_multiplier(self) -> int:
        return self._worker_prefetch_multiplier
    
    @property
    def worker_max_tasks_per_child(self) -> int:
        return self._worker_max_tasks_per_child
    
    @property
    def task_acks_late(self) -> bool:
        return self._task_acks_late
    
    @property
    def beat_scheduler(self) -> str:
        return self._beat_scheduler
    
    @property
    def task_routes(self) -> Dict[str, Dict[str, str]]:
        return self._task_routes
    
    @property
    def task_annotations(self) -> Dict[str, Dict[str, Any]]:
        return self._task_annotations
    
    @property
    def result_expires(self) -> int:
        return self._result_expires
    
    @property
    def task_compression(self) -> str:
        return self._task_compression
    
    @property
    def result_compression(self) -> str:
        return self._result_compression
    
    @property
    def worker_disable_rate_limits(self) -> bool:
        return self._worker_disable_rate_limits
    
    @property
    def worker_send_task_events(self) -> bool:
        return self._worker_send_task_events
    
    @property
    def task_send_sent_event(self) -> bool:
        return self._task_send_sent_event
    
    @property
    def broker_connection_retry(self) -> bool:
        return self._broker_connection_retry
    
    @property
    def broker_connection_retry_on_startup(self) -> bool:
        return self._broker_connection_retry_on_startup
    
    @property
    def broker_connection_max_retries(self) -> int:
        return self._broker_connection_max_retries
    
    @property
    def broker_pool_limit(self) -> int:
        return self._broker_pool_limit
    
    @property
    def redis_max_connections(self) -> int:
        return self._redis_max_connections
    
    @property
    def redis_socket_timeout(self) -> int:
        return self._redis_socket_timeout
    
    @property
    def redis_socket_connect_timeout(self) -> int:
        return self._redis_socket_connect_timeout
    
    @property
    def worker_log_format(self) -> str:
        return self._worker_log_format
    
    @property
    def worker_task_log_format(self) -> str:
        return self._worker_task_log_format
    
    @property
    def task_log_format(self) -> str:
        return self._task_log_format
    
    @property
    def task_ignore_result(self) -> bool:
        return self._task_ignore_result
    
    @property
    def task_store_errors_even_if_ignored(self) -> bool:
        return self._task_store_errors_even_if_ignored
    
    @property
    def task_reject_on_worker_lost(self) -> bool:
        return self._task_reject_on_worker_lost
    
    @property
    def task_default_retry_delay(self) -> int:
        return self._task_default_retry_delay
    
    @property
    def task_max_retries(self) -> int:
        return self._task_max_retries
    
    @property
    def task_default_rate_limit(self) -> str:
        return self._task_default_rate_limit
    
    @property
    def task_inherit_parent_priority(self) -> bool:
        return self._task_inherit_parent_priority
    
    @property
    def beat_sync_every(self) -> int:
        return self._beat_sync_every
    
    @property
    def task_always_eager(self) -> bool:
        return self._task_always_eager
    
    @property
    def imports(self) -> tuple:
        return self._imports
    
    @property
    def include(self) -> tuple:
        return self._include
    
    def as_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return {
            'broker_url': self.broker_url,
            'result_backend': self.result_backend,
            'task_serializer': self.task_serializer,
            'result_serializer': self.result_serializer,
            'accept_content': self.accept_content,
            'timezone': self.timezone,
            'enable_utc': self.enable_utc,
            'task_track_started': self.task_track_started,
            'task_time_limit': self.task_time_limit,
            'task_soft_time_limit': self.task_soft_time_limit,
            'worker_prefetch_multiplier': self.worker_prefetch_multiplier,
            'worker_max_tasks_per_child': self.worker_max_tasks_per_child,
            'task_acks_late': self.task_acks_late,
            'beat_scheduler': self.beat_scheduler,
            'task_routes': self.task_routes,
            'task_annotations': self.task_annotations,
            'result_expires': self.result_expires,
            'task_compression': self.task_compression,
            'result_compression': self.result_compression,
            'worker_disable_rate_limits': self.worker_disable_rate_limits,
            'worker_send_task_events': self.worker_send_task_events,
            'task_send_sent_event': self.task_send_sent_event,
            'broker_connection_retry': self.broker_connection_retry,
            'broker_connection_retry_on_startup': self.broker_connection_retry_on_startup,
            'broker_connection_max_retries': self.broker_connection_max_retries,
            'broker_pool_limit': self.broker_pool_limit,
            'worker_log_format': self.worker_log_format,
            'worker_task_log_format': self.worker_task_log_format,
            'task_log_format': self.task_log_format,
            'task_ignore_result': self.task_ignore_result,
            'task_store_errors_even_if_ignored': self.task_store_errors_even_if_ignored,
            'task_reject_on_worker_lost': self.task_reject_on_worker_lost,
            'task_default_retry_delay': self.task_default_retry_delay,
            'task_max_retries': self.task_max_retries,
            'task_default_rate_limit': self.task_default_rate_limit,
            'task_inherit_parent_priority': self.task_inherit_parent_priority,
            'beat_sync_every': self.beat_sync_every,
            'task_always_eager': self.task_always_eager,
            'imports': self.imports,
            'include': self.include,
        }
    
    def get_queue_names(self) -> list:
        """Get all defined queue names"""
        queues = set()
        for route in self.task_routes.values():
            if 'queue' in route:
                queues.add(route['queue'])
        return sorted(list(queues))
    
    def get_queue_for_task(self, task_name: str) -> Optional[str]:
        """Get queue name for a specific task"""
        # Check exact match
        if task_name in self.task_routes:
            return self.task_routes[task_name].get('queue', 'default')
        
        # Check wildcard match
        for pattern, route in self.task_routes.items():
            if pattern.endswith('.*'):
                prefix = pattern[:-2]
                if task_name.startswith(prefix):
                    return route.get('queue', 'default')
        
        return 'default'


# ===================
# GLOBAL INSTANCE
# ===================

@lru_cache()
def get_celery_config() -> CeleryConfig:
    """Get cached Celery config instance - singleton pattern"""
    return CeleryConfig()


# Default instance - use this throughout the app
celery_config = get_celery_config()


# ===================
# CONVENIENCE EXPORTS
# ===================

# Broker & Backend
CELERY_BROKER_URL = celery_config.broker_url
CELERY_RESULT_BACKEND = celery_config.result_backend

# Serialization
CELERY_TASK_SERIALIZER = celery_config.task_serializer
CELERY_RESULT_SERIALIZER = celery_config.result_serializer
CELERY_ACCEPT_CONTENT = celery_config.accept_content

# Timezone
CELERY_TIMEZONE = celery_config.timezone
CELERY_ENABLE_UTC = celery_config.enable_utc

# Task settings
CELERY_TASK_TRACK_STARTED = celery_config.task_track_started
CELERY_TASK_TIME_LIMIT = celery_config.task_time_limit
CELERY_TASK_SOFT_TIME_LIMIT = celery_config.task_soft_time_limit

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = celery_config.worker_prefetch_multiplier
CELERY_WORKER_MAX_TASKS_PER_CHILD = celery_config.worker_max_tasks_per_child
CELERY_TASK_ACKS_LATE = celery_config.task_acks_late

# Beat scheduler
CELERYBEAT_SCHEDULER = celery_config.beat_scheduler

# Task routes
CELERY_TASK_ROUTES = celery_config.task_routes

# Task annotations
CELERY_TASK_ANNOTATIONS = celery_config.task_annotations

# Result settings
CELERY_RESULT_EXPIRES = celery_config.result_expires
CELERY_RESULT_COMPRESSION = celery_config.result_compression

# Broker settings
CELERY_BROKER_CONNECTION_RETRY = celery_config.broker_connection_retry
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = celery_config.broker_connection_retry_on_startup
CELERY_BROKER_POOL_LIMIT = celery_config.broker_pool_limit

# Get all queues
CELERY_QUEUES = celery_config.get_queue_names()

# Get config as dict for Celery app
CELERY_CONFIG_DICT = celery_config.as_dict()


# ===================
# DYNAMIC CONFIGURATION HELPERS
# ===================

def update_celery_broker_url(new_broker_url: str) -> None:
    """
    Dynamically update Celery broker URL.
    This change will apply to all new tasks.
    
    Usage:
        from config.celery_config import update_celery_broker_url
        update_celery_broker_url('redis://new-host:6379/5')
    """
    celery_config._broker_url = new_broker_url
    CELERY_BROKER_URL = new_broker_url


def update_celery_result_backend(new_backend: str) -> None:
    """
    Dynamically update Celery result backend.
    
    Usage:
        from config.celery_config import update_celery_result_backend
        update_celery_result_backend('redis://new-host:6379/6')
    """
    celery_config._result_backend = new_backend
    CELERY_RESULT_BACKEND = new_backend


def update_task_route(task_pattern: str, queue: str, routing_key: str = None) -> None:
    """
    Dynamically update task routing.
    
    Usage:
        from config.celery_config import update_task_route
        update_task_route('apps.notifications.tasks.*', 'high_priority', 'high.priority')
    """
    route = {'queue': queue}
    if routing_key:
        route['routing_key'] = routing_key
    celery_config._task_routes[task_pattern] = route


def get_task_queue(task_name: str) -> str:
    """Get the queue name for a specific task"""
    return celery_config.get_queue_for_task(task_name)


# ===================
# CELERY BEAT SCHEDULE (Periodic Tasks)
# ===================

CELERY_BEAT_SCHEDULE = {
    # Cleanup expired sessions every hour
    'cleanup-expired-sessions': {
        'task': 'apps.appointments.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Every hour
    },
    
    # Send appointment reminders every 30 minutes
    'send-appointment-reminders': {
        'task': 'apps.notifications.tasks.send_appointment_reminders',
        'schedule': 1800.0,  # Every 30 minutes
    },
    
    # Generate daily reports at midnight
    'generate-daily-reports': {
        'task': 'apps.reports.tasks.generate_daily_report',
        'schedule': {
            'hour': 0,
            'minute': 0,
        },
    },
    
    # Sync appointments every 15 minutes
    'sync-appointments': {
        'task': 'apps.appointments.tasks.sync_appointments',
        'schedule': 900.0,  # Every 15 minutes
    },
    
    # Check pending payments every 5 minutes
    'check-pending-payments': {
        'task': 'apps.appointments.tasks.check_appointment_status',
        'schedule': 300.0,  # Every 5 minutes
    },
}

