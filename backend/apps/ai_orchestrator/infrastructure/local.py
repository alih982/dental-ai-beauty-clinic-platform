import httpx
import json
from typing import Dict, Any, AsyncIterator
from ..domain.ports import AIManager, Prompt, Completion

class LocalProvider(AIManager):
    """
    Concrete implementation of AIManager for Local Inference (Ollama).
    """
    
    def __init__(self, host: str, model: str = "gemma2"):
        self.host = host
        self.model = model
        self.api_url = f"{host}/api/generate"

    async def generate_response(self, prompt: Prompt) -> Completion:
        """
        Generates a response from local Ollama instance (async).
        """
        # MLflow Tracing
        from config.mlflow_config import MLflowTracer
        
        parameters = {
            "model": self.model,
            "provider": "local/ollama",
            "prompt_length": len(prompt.text),
            "options": prompt.parameters
        }

        with MLflowTracer("generate_response", parameters) as run:
            payload = {
                "model": self.model,
                "prompt": prompt.text,
                "system": prompt.system_prompt,
                "stream": False,
                "options": prompt.parameters
            }
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(self.api_url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    content = data.get("response", "")
                    
                    # Log completion metrics
                    if run:
                        import mlflow
                        mlflow.log_metric("completion_length", len(content))
                        dt = data.get("total_duration")
                        if dt:
                            mlflow.log_metric("latency_ns", dt)

                    return Completion(
                        content=content,
                        model_used=self.model,
                        raw_response=data
                    )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Ollama at {self.host}: {str(e)}")

    async def stream_response(self, prompt: Prompt) -> AsyncIterator[str]:
        """
        Streams response from local Ollama instance (async).
        """
        from config.mlflow_config import MLflowTracer
        
        with MLflowTracer("stream_response", {"model": self.model, "streaming": True}):
            payload = {
                "model": self.model,
                "prompt": prompt.text,
                "system": prompt.system_prompt,
                "stream": True,
                "options": prompt.parameters
            }
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", self.api_url, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                chunk = data.get("response", "")
                                if chunk:
                                    yield chunk
            except Exception as e:
                 yield f" (Streaming failed: {str(e)})"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "local",
            "model": self.model,
            "host": self.host
        }
