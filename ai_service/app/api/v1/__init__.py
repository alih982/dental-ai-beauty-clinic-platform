"""API v1 router initialization"""
from fastapi import APIRouter

# Import individual routers
from . import chat, health

# Re-export for convenience
__all__ = ['chat', 'health']
