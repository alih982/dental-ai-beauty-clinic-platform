"""Health check endpoints"""
from fastapi import APIRouter
from datetime import datetime

from app.domain.schemas import HealthCheckResponse
from app.core.provider import AIProviderFactory
from app.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    Verifies the active AI provider is healthy.
    """
    provider = AIProviderFactory.get_provider()
    is_healthy = await provider.health_check()
    
    return HealthCheckResponse(
        status="healthy" if is_healthy else "degraded",
        model=settings.OLLAMA_MODEL,
        model_available=is_healthy
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.now()}
