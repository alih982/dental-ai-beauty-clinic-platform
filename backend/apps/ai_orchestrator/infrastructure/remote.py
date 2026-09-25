import httpx
import json
from typing import Dict, Any, AsyncIterator
from ..domain.ports import AIManager, Prompt, Completion

class RemoteProvider(AIManager):
    """
    Standardized AI Provider that communicates with the Smart Health AI Service (FastAPI).
    This acts as a gateway to centralized medical logic and streaming.
    """
    
    def __init__(self, endpoint: str = "http://maggicaihub.com:8001/api/v1/chat"):
        self.endpoint = endpoint

    async def generate_response(self, prompt: Prompt) -> Completion:
        """
        Sends a non-streaming request to the AI Service (async).
        """
        payload = {
            "message": prompt.text,
            "history": [],
            "enable_rag": getattr(prompt, 'parameters', {}).get('enable_rag', False)
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                
                return Completion(
                    content=data.get("response", ""),
                    model_used="gemma2:2b (via AI Service)",
                    raw_response=data
                )
        except Exception as e:
            raise ConnectionError(f"AI Service Gateway Error: {str(e)}")

    async def stream_response(self, prompt: Prompt) -> AsyncIterator[str]:
        """
        Streams response from the AI Service via Server-Sent Events (SSE) (async).
        """
        payload = {
            "message": prompt.text,
            "history": [],
            "enable_rag": getattr(prompt, 'parameters', {}).get('enable_rag', False)
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", f"{self.endpoint}/stream", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith('data: '):
                                try:
                                    json_str = line[6:]
                                    data = json.loads(json_str)
                                    if data.get('done'):
                                        break
                                    chunk = data.get('chunk', '')
                                    if chunk:
                                        yield chunk
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            yield f" (Connection error: {str(e)})"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "remote_gateway",
            "endpoint": self.endpoint
        }
