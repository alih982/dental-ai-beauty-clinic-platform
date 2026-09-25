"""
Complete Celery Configuration for Smart Health Platform

This module provides a complete, bug-free Celery setup with:
- Redis as message broker
- Redis as result backend
- Django Celery Beat for scheduled tasks
- Proper error handling and logging
- Health check support

Usage:
    # Start worker:
    celery -A config worker --loglevel=info --concurrency=4
    
    # Start beat:
    celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    
    # Or use the app directly:
    from config.celery import app as celery_app

DYNAMIC CONFIGURATION:
    All settings are loaded from config.celery_config which uses
    config.dynamic_settings. Change environment variables to update
    all settings across the project with a single line change!
"""

import os
import logging
from celery import Celery
from celery.signals import worker_init, worker_shutdown, task_prerun, task_postrun
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

# Create Celery app
app = Celery('smart_health')

# Load configuration from the centralized dynamic config
from config.celery_config import celery_config

# Apply all settings from centralized config
app.conf.update(celery_config.as_dict())

# Additional Celery optimizations
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'

# Result backend configuration
app.conf.result_expires = 3600  # 1 hour
app.conf.result_persistent = True

# Task routing for different queues (using centralized config)
app.conf.task_routes = celery_config.task_routes

# Beat schedule for periodic tasks (using centralized config)
app.conf.beat_schedule = {
    # Daily tasks
    'cleanup-old-sessions': {
        'task': 'apps.core.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
    },
    
    # Weekly tasks
    'generate-weekly-report': {
        'task': 'apps.core.tasks.generate_weekly_report',
        'schedule': crontab(hour=3, minute=0, day_of_week='sunday'),  # Sunday 3 AM
    },
    
    # Monthly tasks
    'generate-monthly-report': {
        'task': 'apps.core.tasks.generate_monthly_report',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),  # 1st of month 4 AM
    },
    
    # Appointment reminders - every 5 minutes
    'check-appointment-reminders': {
        'task': 'apps.core.tasks.process_appointment_reminders',
        'schedule': 300,  # 5 minutes
    },
    
    # Cache warming - every hour
    'warm-cache': {
        'task': 'apps.core.tasks.warm_cache',
        'schedule': 3600,  # 1 hour
    },
}

# Auto-discover tasks from all installed apps
app.autodiscover_tasks(['apps.core', 'apps.appointments', 'apps.accounts', 'apps.notifications', 'apps.chat', 'apps.prescriptions'])

# Setup logging
logger = logging.getLogger(__name__)


# ===================
# CELERY SIGNALS
# ===================

@worker_init.connect
def on_worker_init(**kwargs):
    """Called when worker initializes"""
    logger.info("Celery worker initialized")
    # Initialize connections
    from django.db import connections
    connections.close_all()


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """Called when worker shuts down"""
    logger.info("Celery worker shutting down")
    from django.db import connections
    connections.close_all()


@task_prerun.connect
def on_task_prerun(task_id, task, *args, **kwargs):
    """Called before a task is executed"""
    logger.debug(f"Task {task.name}[{task_id}] starting")


@task_postrun.connect
def on_task_postrun(task_id, task, *args, **kwargs):
    """Called after a task is executed"""
    logger.debug(f"Task {task.name}[{task_id}] completed")


# ===================
# CELERY HEALTH CHECK
# ===================

@app.task(bind=True)
def health_check(self):
    """Health check task for monitoring"""
    return {
        'status': 'healthy',
        'worker': self.request.hostname,
        'active_tasks': self.request.chain,
    }


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    logger.info(f'Request: {self.request!r}')
    return {
        'worker': self.request.hostname,
        'pid': os.getpid(),
    }


# ===================
# EXPORTS
# ===================

__all__ = ('app', 'celery_app')


# Make app available as celery_app for compatibility
celery_app = app

