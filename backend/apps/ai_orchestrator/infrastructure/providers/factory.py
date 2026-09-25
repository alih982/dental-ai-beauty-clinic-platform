"""
AI Provider Factory

Implements Factory pattern for creating AI providers based on configuration.
Supports multiple providers and easy extension.
"""
from typing import Dict, Type
from django.conf import settings

from .base import BaseAIProvider
from .gemma import GemmaProvider
from .openai import OpenAIProvider
from ...domain.entities import AIProviderType, AIProviderConfig
from ...domain.exceptions import AIProviderException


class AIProviderFactory:
    """
    Factory for creating AI provider instances.
    
    Usage:
        config = AIProviderConfig(
            provider_type=AIProviderType.GEMMA,
            model_name="gemma2:latest",
            base_url="http://maggicaihub.com:11434"
        )
        provider = AIProviderFactory.create(config)
    """
    
    # Registry of available providers
    _providers: Dict[AIProviderType, Type[BaseAIProvider]] = {
        AIProviderType.GEMMA: GemmaProvider,
        AIProviderType.LOCAL: GemmaProvider,  # Alias for Gemma
        AIProviderType.OPENAI: OpenAIProvider,
    }
    
    @classmethod
    def create(cls, config: AIProviderConfig) -> BaseAIProvider:
        """
        Create an AI provider instance.
        
        Args:
            config: Provider configuration
            
        Returns:
            Configured AI provider instance
            
        Raises:
            AIProviderException: If provider type is not supported
        """
        provider_class = cls._providers.get(config.provider_type)
        
        if not provider_class:
            raise AIProviderException(
                f"Unsupported provider type: {config.provider_type}. "
                f"Available providers: {list(cls._providers.keys())}"
            )
        
        return provider_class(config)
    
    @classmethod
    def create_from_settings(cls) -> BaseAIProvider:
        """
        Create provider from Django settings.
        
        Reads configuration from settings.py:
        - AI_PROVIDER_TYPE
        - AI_MODEL_NAME
        - AI_API_KEY
        - AI_BASE_URL
        
        Returns:
            Configured AI provider instance
        """
        provider_type_str = getattr(settings, 'AI_PROVIDER_TYPE', 'local')
        
        # Map string to enum
        provider_type_map = {
            'gemma': AIProviderType.GEMMA,
            'local': AIProviderType.LOCAL,
            'openai': AIProviderType.OPENAI,
            'claude': AIProviderType.CLAUDE,
        }
        
        provider_type = provider_type_map.get(
            provider_type_str.lower(),
            AIProviderType.LOCAL
        )
        
        config = AIProviderConfig(
            provider_type=provider_type,
            model_name=getattr(settings, 'AI_MODEL_NAME', 'gemma2:latest'),
            api_key=getattr(settings, 'AI_API_KEY', None),
            base_url=getattr(settings, 'AI_BASE_URL', 'http://maggicaihub.com:11434'),
            timeout=getattr(settings, 'AI_TIMEOUT', 30),
            max_retries=getattr(settings, 'AI_MAX_RETRIES', 3)
        )
        
        return cls.create(config)
    
    @classmethod
    def register_provider(
        cls,
        provider_type: AIProviderType,
        provider_class: Type[BaseAIProvider]
    ) -> None:
        """
        Register a new provider type.
        
        Allows extending the factory with custom providers.
        
        Args:
            provider_type: Provider type enum
            provider_class: Provider class to register
        """
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get list of available provider types.
        
        Returns:
            List of provider type names
        """
        return [provider.value for provider in cls._providers.keys()]
