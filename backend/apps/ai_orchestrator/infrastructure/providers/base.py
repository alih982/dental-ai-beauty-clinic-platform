"""
Base AI Provider Implementation

Provides common functionality for all AI providers.
Follows Template Method pattern for shared behavior.
"""
import asyncio
import time
from typing import AsyncIterator, Dict, Any
from abc import abstractmethod

from ...domain.ports import IAIProvider
from ...domain.entities import AIRequest, AIResponse, AIProviderConfig, AIProviderType
from ...domain.exceptions import (
    AIProviderException,
    AIProviderTimeoutException,
    AIProviderUnavailableException
)


class BaseAIProvider(IAIProvider):
    """
    Abstract base class for AI providers.
    
    Implements common functionality like:
    - Timeout handling
    - Retry logic
    - Health check caching
    - Metrics collection
    """
    
    def __init__(self, config: AIProviderConfig):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        super().__init__(config)
        self._last_health_check: float = 0
        self._health_check_cache: bool = False
        self._health_check_ttl: int = 60  # Cache health status for 60 seconds
    
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """
        Generate response with timeout and retry logic.
        
        Args:
            request: AI generation request
            
        Returns:
            Complete AI response
            
        Raises:
            AIProviderTimeoutException: If request times out
            AIProviderException: For other errors
        """
        start_time = time.time()
        
        for attempt in range(self.config.max_retries):
            try:
                response = await asyncio.wait_for(
                    self._generate_implementation(request),
                    timeout=self.config.timeout
                )
                
                # Record latency
                response.latency_ms = (time.time() - start_time) * 1000
                return response
                
            except asyncio.TimeoutError:
                if attempt == self.config.max_retries - 1:
                    raise AIProviderTimeoutException(
                        f"Request timed out after {self.config.timeout}s"
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise AIProviderException(f"Failed after {self.config.max_retries} attempts: {str(e)}")
                await asyncio.sleep(2 ** attempt)
    
    async def stream_response(self, request: AIRequest) -> AsyncIterator[str]:
        """
        Stream response with timeout handling.
        
        Args:
            request: AI generation request
            
        Yields:
            Response chunks
        """
        try:
            async for chunk in asyncio.wait_for(
                self._stream_implementation(request),
                timeout=self.config.timeout
            ):
                yield chunk
        except asyncio.TimeoutError:
            raise AIProviderTimeoutException(f"Streaming timed out after {self.config.timeout}s")
    
    async def health_check(self) -> bool:
        """
        Check provider health with caching.
        
        Returns:
            True if healthy
        """
        current_time = time.time()
        
        # Return cached result if still valid
        if current_time - self._last_health_check < self._health_check_ttl:
            return self._health_check_cache
        
        # Perform actual health check
        try:
            is_healthy = await self._health_check_implementation()
            self._health_check_cache = is_healthy
            self._last_health_check = current_time
            return is_healthy
        except Exception:
            self._health_check_cache = False
            self._last_health_check = current_time
            return False
    
    # Abstract methods that subclasses MUST implement
    
    @abstractmethod
    async def _generate_implementation(self, request: AIRequest) -> AIResponse:
        """Actual generation logic - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def _stream_implementation(self, request: AIRequest) -> AsyncIterator[str]:
        """Actual streaming logic - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def _health_check_implementation(self) -> bool:
        """Actual health check logic - to be implemented by subclasses"""
        pass
