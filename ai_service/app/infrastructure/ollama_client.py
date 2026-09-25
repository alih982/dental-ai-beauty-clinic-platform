"""
Ollama Client Wrapper - Async integration with llama3.2
"""
import ollama
from ollama import AsyncClient
from typing import AsyncGenerator, List, Dict, Any
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Async service for interacting with Ollama.
    Provides streaming and non-streaming chat capabilities.
    """
    
    def __init__(self):
        self.client = AsyncClient(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL
        logger.info(f"Initialized OllamaService with model: {self.model}")

    async def ensure_model_is_pulled(self):
        """Ensure the required model is available, pull if missing"""
        if not settings.AUTO_PULL_MODEL:
            return

        try:
            logger.info(f"Checking for model: {self.model}...")
            if await self.is_model_available():
                logger.info(f"Model {self.model} is already available.")
                return

            logger.info(f"Model {self.model} not found. Starting automatic pull...")
            # We use synchronous-like call for progress or just await
            async for progress in await self.client.pull(model=self.model, stream=True):
                status = progress.get('status', '')
                if 'completed' in status or 'success' in status:
                    logger.info(f"Successfully pulled {self.model}")
                elif 'pulling' in status:
                    # Log pulling progress occasionally to avoid spam
                    pass
        except Exception as e:
            logger.error(f"Failed to pull model {self.model}: {e}")

    async def is_model_available(self) -> bool:
        """Check if the model is available"""
        try:
            models = await self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            return self.model in model_names
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        system_prompt: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from LLM.
        
        Args:
            messages: Chat history in format [{"role": "user", "content": "..."}]
            temperature: Randomness (0-1). Higher = more creative
            system_prompt: System instructions for the model
        
        Yields:
            str: Chunks of the response as they arrive
        """
        try:
            # Add system prompt if provided
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            # Stream response
            async for chunk in await self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": temperature or settings.TEMPERATURE,
                    "top_p": settings.TOP_P,
                    "num_predict": settings.MAX_TOKENS
                }
            ):
                if chunk.get('done', False):
                    break
                
                if content := chunk.get('message', {}).get('content'):
                    yield content
        
        except Exception as e:
            logger.error(f"Error in stream_chat: {e}", exc_info=True)
            yield f"خطا: {str(e)}"
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        system_prompt: str = None
    ) -> str:
        """
        Non-streaming chat response.
        
        Returns complete response as a single string.
        """
        try:
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                stream=False,
                options={
                    "temperature": temperature or settings.TEMPERATURE,
                    "top_p": settings.TOP_P,
                    "num_predict": settings.MAX_TOKENS
                }
            )
            
            return response['message']['content']
        
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return f"خطا در دریافت پاسخ: {str(e)}"
    
    async def generate_medical_summary(
        self,
        symptoms: str,
        patient_history: str = None
    ) -> str:
        """
        Generate medical summary from symptoms.
        
        Specialized for medical context.
        """
        system_prompt = """شما یک دستیار پزشکی هوشمند هستید که به زبان فارسی پاسخ می‌دهید.
وظیفه شما تحلیل علائم بیمار و ارائه اطلاعات کلی است.
توجه: پاسخ‌های شما صرفاً جنبه اطلاعاتی دارند و جایگزین مشاوره پزشکی نیست.
مراجعه به پزشک متخصص الزامی است."""
        
        prompt = f"علائم بیمار: {symptoms}"
        if patient_history:
            prompt += f"\n\nسابقه پزشکی: {patient_history}"
        
        prompt += "\n\nلطفاً یک خلاصه کوتاه و مفید ارائه دهید."
        
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, system_prompt=system_prompt, temperature=0.5)
    
    async def suggest_specialists(self, symptoms: str) -> List[str]:
        """
        Suggest medical specialists based on symptoms.
        """
        system_prompt = """شما یک دستیار پزشکی هستید. بر اساس علائم، نام تخصص‌های پزشکی مرتبط را به زبان فارسی لیست کنید.
فقط نام تخصص‌ها را بنویسید، هر کدام در یک خط."""
        
        prompt = f"علائم: {symptoms}\n\nتخصص‌های پزشکی پیشنهادی:"
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, system_prompt=system_prompt, temperature=0.3)
        
        # Parse specialists from response
        specialists = [
            line.strip().lstrip('-').strip() 
            for line in response.split('\n') 
            if line.strip()
        ]
        
        return specialists[:5]  # Return top 5


# Singleton instance
ollama_service = OllamaService()
