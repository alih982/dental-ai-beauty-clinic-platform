"""
AI Orchestrator Domain Ports (Interfaces)

These interfaces define contracts for AI providers and repositories.
Following the Ports & Adapters pattern for clean architecture.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any
from .entities import AIRequest, AIResponse, AIProviderConfig


class IAIProvider(ABC):
    """
    Port (interface) for AI providers.
    
    All AI providers (Gemma, OpenAI, Claude) must implement this interface.
    This allows swapping providers without changing business logic.
    """
    
    def __init__(self, config: AIProviderConfig):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
    
    @abstractmethod
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """
        Generate a complete response for the given request.
        
        Args:
            request: AI generation request
            
        Returns:
            Complete AI response
            
        Raises:
            AIProviderException: If generation fails
        """
        pass
    
    @abstractmethod
    async def stream_response(
        self, 
        request: AIRequest
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response for the given request.
        
        Args:
            request: AI generation request
            
        Yields:
            Response chunks as they're generated
            
        Raises:
            AIProviderException: If streaming fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available and healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary containing model metadata
        """
        pass


class IAIRepository(ABC):
    """
    Port (interface) for AI interaction logging.
    
    Repositories handle persistence of AI interactions for audit,
    analytics, and improvement purposes.
    """
    
    @abstractmethod
    async def log_interaction(
        self,
        request: AIRequest,
        response: AIResponse,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Log an AI interaction.
        
        Args:
            request: Original request
            response: Generated response
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            ID of logged interaction
        """
        pass
    
    @abstractmethod
    async def get_interaction_history(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Retrieve interaction history.
        
        Args:
            user_id: Filter by user
            session_id: Filter by session
            limit: Maximum number of interactions to return
            
        Returns:
            List of interaction records
        """
        pass


class IAIMetricsCollector(ABC):
    """
    Port (interface) for collecting AI metrics.
    
    Enables monitoring of AI performance, costs, and usage.
    """
    
    @abstractmethod
    async def record_request(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        latency_ms: float,
        success: bool
    ) -> None:
        """
        Record metrics for an AI request.
        
        Args:
            provider: Provider name
            model: Model name
            tokens_used: Number of tokens consumed
            latency_ms: Request latency in milliseconds
            success: Whether request succeeded
        """
        pass
    
    @abstractmethod
    async def get_usage_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dictionary containing usage statistics
        """
        pass


# Compatibility Interfaces (Legacy support)
class Prompt(ABC):
    text: str
    system_prompt: Optional[str]
    parameters: Dict[str, Any]

class Completion(ABC):
    content: str
    model_used: str
    raw_response: Dict[str, Any]

class AIManager(ABC):
    @abstractmethod
    async def generate_response(self, prompt: Prompt) -> Completion:
        pass

    @abstractmethod
    def stream_response(self, prompt: Prompt) -> AsyncIterator[str]:
        pass

class AIModelType:
    LOCAL = "local"
    MOCK = "mock"
    OPENAI = "openai"
    GATEWAY = "gateway"
