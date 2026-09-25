"""
OpenAI Provider Implementation

Implements OpenAI GPT models integration.
Supports GPT-4, GPT-3.5-turbo, and streaming.
"""
import aiohttp
import json
from typing import AsyncIterator, Dict, Any

from .base import BaseAIProvider
from ...domain.entities import AIRequest, AIResponse, AIProviderType
from ...domain.exceptions import (
    AIProviderException,
    QuotaExceededException,
    ModelNotFoundException
)


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI provider for GPT models.
    
    Features:
    - Multiple model support (GPT-4, GPT-3.5)
    - Function calling
    - Streaming responses
    - Token usage tracking
    """
    
    async def _generate_implementation(self, request: AIRequest) -> AIResponse:
        """
        Generate response using OpenAI API.
        
        Args:
            request: AI generation request
            
        Returns:
            Complete AI response
        """
        url = "http://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = self._build_messages(request)
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 429:
                        raise QuotaExceededException("OpenAI API quota exceeded")
                    elif response.status == 404:
                        raise ModelNotFoundException(f"Model {self.config.model_name} not found")
                    elif response.status != 200:
                        error_text = await response.text()
                        raise AIProviderException(
                            f"OpenAI API error ({response.status}): {error_text}"
                        )
                    
                    data = await response.json()
                    choice = data["choices"][0]
                    
                    return AIResponse(
                        content=choice["message"]["content"],
                        provider=AIProviderType.OPENAI,
                        model=data.get("model", self.config.model_name),
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        metadata={
                            "finish_reason": choice.get("finish_reason"),
                            "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                            "completion_tokens": data.get("usage", {}).get("completion_tokens", 0)
                        }
                    )
                    
        except aiohttp.ClientError as e:
            raise AIProviderException(f"Network error: {str(e)}")
    
    async def _stream_implementation(self, request: AIRequest) -> AsyncIterator[str]:
        """
        Stream response using OpenAI API.
        
        Args:
            request: AI generation request
            
        Yields:
            Response chunks
        """
        url = "http://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = self._build_messages(request)
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AIProviderException(f"OpenAI streaming error: {error_text}")
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            line = line[6:]
                            if line == '[DONE]':
                                break
                            try:
                                data = json.loads(line)
                                delta = data['choices'][0]['delta']
                                if 'content' in delta:
                                    yield delta['content']
                            except json.JSONDecodeError:
                                continue
                                
        except aiohttp.ClientError as e:
            raise AIProviderException(f"Streaming error: {str(e)}")
    
    async def _health_check_implementation(self) -> bool:
        """
        Check if OpenAI API is accessible.
        
        Returns:
            True if API is accessible
        """
        url = "http://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information"""
        return {
            "provider": "openai",
            "model": self.config.model_name,
            "type": "gpt",
            "supports_streaming": True,
            "supports_function_calling": "gpt-4" in self.config.model_name or "gpt-3.5" in self.config.model_name,
            "context_window": 128000 if "gpt-4" in self.config.model_name else 16385
        }
    
    def _build_messages(self, request: AIRequest) -> list:
        """Build OpenAI message format"""
        messages = []
        
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
