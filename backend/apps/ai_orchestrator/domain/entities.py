"""
AI Orchestrator Domain Entities

This module defines the core domain entities for AI interactions.
Following DDD principles, these are pure business objects without framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class AIProviderType(str, Enum):
    """Supported AI provider types"""
    GEMMA = "gemma"
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"  # Ollama


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Represents a single message in conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIRequest:
    """
    Domain entity representing an AI generation request.
    
    Attributes:
        prompt: User's input/question
        system_prompt: Optional system context
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum response length
        conversation_history: Previous messages for context
        metadata: Additional request information
    """
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    conversation_history: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request parameters"""
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")


@dataclass
class AIResponse:
    """
    Domain entity representing AI generation response.
    
    Attributes:
        content: Generated text
        provider: Which AI provider generated this
        model: Specific model used
        tokens_used: Token consumption
        latency_ms: Response time in milliseconds
        metadata: Additional response information
    """
    content: str
    provider: AIProviderType
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AIProviderConfig:
    """
    Configuration for AI provider.
    
    Attributes:
        provider_type: Type of provider (Gemma, OpenAI, etc.)
        model_name: Specific model to use
        api_key: Authentication key (if needed)
        base_url: API endpoint
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts
        additional_params: Provider-specific configuration
    """
    provider_type: AIProviderType
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    additional_params: Dict[str, Any] = field(default_factory=dict)
