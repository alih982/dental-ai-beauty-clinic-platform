"""Notifications app initialization"""

def get_whatsapp_service():
    """Lazy import for whatsapp_service"""
    from .services.whatsapp_service import whatsapp_service
    return whatsapp_service

def get_scheduling_service():
    """Lazy import for scheduling_service"""
    from .services.scheduling_service import scheduling_service
    return scheduling_service

# For backwards compatibility, provide lazy access
class _LazyService:
    def __getattr__(self, name):
        if name == 'whatsapp_service':
            return get_whatsapp_service()
        elif name == 'scheduling_service':
            return get_scheduling_service()
        raise AttributeError(f"module has no attribute '{name}'")

whatsapp_service = _LazyService()
scheduling_service = _LazyService()

__all__ = ['whatsapp_service', 'scheduling_service']
