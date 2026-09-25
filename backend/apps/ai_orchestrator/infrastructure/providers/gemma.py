"""
Gemma AI Provider (via Ollama)

Implements Gemma/Llama model integration through Ollama.
Supports both local and remote Ollama instances.
"""
import aiohttp
import json
from typing import AsyncIterator, Dict, Any, List

from .base import BaseAIProvider
from ...domain.entities import (
    AIRequest, 
    AIResponse, 
    AIProviderType,
    Message,
    MessageRole
)
from ...domain.exceptions import (
    AIProviderException,
    AIProviderUnavailableException,
    ModelNotFoundException
)


class GemmaProvider(BaseAIProvider):
    """
    Gemma/Llama provider using Ollama backend.
    
    Supports streaming and non-streaming generation.
    Handles conversation context automatically.
    """
    
    async def _generate_implementation(self, request: AIRequest) -> AIResponse:
        """
        Generate complete response using Ollama API.
        
        Args:
            request: AI generation request
            
        Returns:
            Complete AI response
            
        Raises:
            AIProviderException: If generation fails
        """
        url = f"{self.config.base_url}/api/generate"
        
        # Build messages from conversation history
        messages = self._build_messages(request)
        
        payload = {
            "model": self.config.model_name,
            "prompt": request.prompt,
            "system": request.system_prompt or "",
            "temperature": request.temperature,
            "stream": False,
            "options": {
                "num_predict": request.max_tokens
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AIProviderException(
                            f"Ollama API error ({response.status}): {error_text}"
                        )
                    
                    data = await response.json()
                    
                    return AIResponse(
                        content=data.get("response", ""),
                        provider=AIProviderType.GEMMA,
                        model=self.config.model_name,
                        tokens_used=data.get("eval_count", 0),
                        metadata={
                            "total_duration": data.get("total_duration"),
                            "load_duration": data.get("load_duration"),
                            "eval_duration": data.get("eval_duration")
                        }
                    )
                    
        except aiohttp.ClientError as e:
            raise AIProviderException(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise AIProviderException(f"Invalid response format: {str(e)}")
    
    async def _stream_implementation(self, request: AIRequest) -> AsyncIterator[str]:
        """
        Stream response using Ollama API.
        
        Args:
            request: AI generation request
            
        Yields:
            Response chunks as they're generated
        """
        url = f"{self.config.base_url}/api/generate"
        
        payload = {
            "model": self.config.model_name,
            "prompt": request.prompt,
            "system": request.system_prompt or "",
            "temperature": request.temperature,
            "stream": True,
            "options": {
                "num_predict": request.max_tokens
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AIProviderException(
                            f"Ollama streaming error ({response.status}): {error_text}"
                        )
                    
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                            except json.JSONDecodeError:
                                continue
                                
        except aiohttp.ClientError as e:
            raise AIProviderException(f"Streaming error: {str(e)}")
    
    async def _health_check_implementation(self) -> bool:
        """
        Check if Ollama is available and model is loaded.
        
        Returns:
            True if healthy and model available
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Ollama is running
                async with session.get(f"{self.config.base_url}/api/tags") as response:
                    if response.status != 200:
                        return False
                    
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    # Check if our model is available
                    return self.config.model_name in models
                    
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Gemma model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "provider": "ollama",
            "model": self.config.model_name,
            "type": "gemma",
            "base_url": self.config.base_url,
            "supports_streaming": True,
            "supports_function_calling": False,
            "context_window": 8192  # Default for most Gemma models
        }
    
    def _build_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """
        Build message format from conversation history.
        
        Args:
            request: AI request with conversation history
            
        Returns:
            List of formatted messages
        """
        messages = []
        
        # Add system message if present
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # Add conversation history
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Add current prompt
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
