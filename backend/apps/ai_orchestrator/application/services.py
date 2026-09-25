"""
AI Orchestration Service (Application Layer)

This service coordinates AI operations and implements business logic.
"""
from typing import AsyncIterator, Optional, Dict, Any
import time

from ..domain.ports import IAIProvider, IAIRepository, IAIMetricsCollector
from ..domain.entities import AIRequest, AIResponse, Message, MessageRole
from ..domain.exceptions import AIProviderException
from ..infrastructure.providers.factory import AIProviderFactory


class AIOrchestrationService:
    """
    Application service for AI operations.
    
    Responsibilities:
    - Coordinate AI providers
    - Log interactions
    - Collect metrics
    - Handle errors gracefully
    """
    
    def __init__(
        self,
        provider: Optional[IAIProvider] = None,
        repository: Optional[IAIRepository] = None,
        metrics_collector: Optional[IAIMetricsCollector] = None
    ):
        """
        Initialize AI orchestration service.
        
        Args:
            provider: AI provider (defaults to factory-created)
            repository: Interaction repository
            metrics_collector: Metrics collector
        """
        self.provider = provider or AIProviderFactory.create_from_settings()
        self.repository = repository
        self.metrics_collector = metrics_collector
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        conversation_history: list[Message] = None
    ) -> AIResponse:
        """
        Generate AI response with logging and metrics.
        
        Args:
            prompt: User's question/input
            system_prompt: System context
            temperature: Creativity level
            max_tokens: Maximum response length
            user_id: Optional user ID for logging
            session_id: Optional session ID for logging
            conversation_history: Previous messages
            
        Returns:
            AI response
            
        Raises:
            AIProviderException: If generation fails
        """
        start_time = time.time()
        
        # Build request
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history or []
        )
        
        try:
            # Generate response
            response = await self.provider.generate_response(request)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            response.latency_ms = latency_ms
            
            # Log interaction
            if self.repository:
                await self.repository.log_interaction(
                    request=request,
                    response=response,
                    user_id=user_id,
                    session_id=session_id
                )
            
            # Record metrics
            if self.metrics_collector:
                await self.metrics_collector.record_request(
                    provider=response.provider.value,
                    model=response.model,
                    tokens_used=response.tokens_used,
                    latency_ms=latency_ms,
                    success=True
                )
            
            return response
            
        except AIProviderException as e:
            # Record failed metrics
            if self.metrics_collector:
                await self.metrics_collector.record_request(
                    provider=self.provider.config.provider_type.value,
                    model=self.provider.config.model_name,
                    tokens_used=0,
                    latency_ms=(time.time() - start_time) * 1000,
                    success=False
                )
            raise
    
    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        conversation_history: list[Message] = None
    ) -> AsyncIterator[str]:
        """
        Stream AI response with real-time updates.
        
        Args:
            prompt: User's question/input
            system_prompt: System context
            temperature: Creativity level
            max_tokens: Maximum response length
            conversation_history: Previous messages
            
        Yields:
            Response chunks as they're generated
        """
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history or []
        )
        
        try:
            full_response = ""
            
            async for chunk in self.provider.stream_response(request):
                full_response += chunk
                yield chunk
            
            # After streaming completes, log the full response
            if self.repository and full_response:
                response = AIResponse(
                    content=full_response,
                    provider=self.provider.config.provider_type,
                    model=self.provider.config.model_name,
                    tokens_used=len(full_response.split())  # Rough estimate
                )
                
                await self.repository.log_interaction(
                    request=request,
                    response=response
                )
                
        except AIProviderException as e:
            # Log error and re-raise
            yield f"\n\n[Error: {str(e)}]"
            raise
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about current AI model.
        
        Returns:
            Model metadata
        """
        return self.provider.get_model_info()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check AI service health.
        
        Returns:
            Health status
        """
        is_healthy = await self.provider.health_check()
        
        return {
            "healthy": is_healthy,
            "provider": self.provider.config.provider_type.value,
            "model": self.provider.config.model_name,
            "timestamp": time.time()
        }


# Singleton instance for easy access
_ai_service: Optional[AIOrchestrationService] = None


def get_ai_service() -> AIOrchestrationService:
    """
    Get or create AI service singleton.
    
    Returns:
        AI orchestration service instance
    """
    global _ai_service
    
    if _ai_service is None:
        _ai_service = AIOrchestrationService()
    
    return _ai_service
