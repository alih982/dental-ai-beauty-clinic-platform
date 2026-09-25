from typing import Optional
from ..domain.ports import AIManager, AIModelType
from .local import LocalProvider
from .remote import RemoteProvider
from .mock import MockProvider

class AIFactory:
    """
    Factory to instantiate the correct AI Provider strategy.
    """
    
    @staticmethod
    def create(provider_type: str, **kwargs) -> AIManager:
        if provider_type == AIModelType.LOCAL:
            return LocalProvider(
                host=kwargs.get("host", "http://maggicaihub.com:11434"),
                model=kwargs.get("model", "gemma2:2b")
            )
        elif provider_type == AIModelType.GATEWAY:
            return RemoteProvider(
                endpoint=kwargs.get("endpoint", "http://maggicaihub.com:8001/api/v1/chat")
            )
        elif provider_type == AIModelType.MOCK:
            return MockProvider()
        # elif provider_type == AIModelType.OPENAI:
        #     return OpenAIProvider(api_key=kwargs.get("api_key"))
        else:
            raise ValueError(f"Unsupported AI Provider: {provider_type}")
