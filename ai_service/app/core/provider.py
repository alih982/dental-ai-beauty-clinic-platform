# ============================================================
# app/core/provider.py
# AI Provider for Fine-Tuned Gemma 2 Model (Local)
# ============================================================
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.config import settings

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 1. کلاس انتزاعی AIProvider
# ----------------------------------------------------------------------
class AIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        message: str,
        history: List[dict] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generates streaming response from AI model."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Checks if the AI model is healthy."""
        pass


# ----------------------------------------------------------------------
# 2. سرویس بارگذاری و اجرای مدل فاین‌تیون شده (Gemma 2)
# ----------------------------------------------------------------------
class FineTunedModelService:
    _instance = None
    _model = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None:
            model_path = settings.AI_MODEL_PATH  # e.g., "app/ai_model" or HuggingFace repo
            logger.info(f"Loading fine-tuned Gemma 2 model from {model_path}...")

            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path, trust_remote_code=True
            )

            # Device configuration
            if torch.cuda.is_available():
                torch_dtype = torch.bfloat16
                device_map = "auto"
            else:
                torch_dtype = torch.float32
                device_map = None

            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch_dtype,
                device_map=device_map,
                trust_remote_code=True,
            )

            # Set pad token if missing
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            logger.info("Model loaded successfully.")

    async def generate(
        self,
        message: str,
        history: List[dict] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Generates streaming response from the fine-tuned model."""
        self._load_model()

        if system_prompt is None:
            system_prompt = "شما یک دستیار پزشکی حاذق هستید که به زبان فارسی پاسخ می‌دهید."

        # Build prompt in Gemma's chat format
        prompt = f"<bos><start_of_turn>system\n{system_prompt}<end_of_turn>\n"
        if history:
            # Keep only last 4 turns to avoid excessive length
            for turn in history[-4:]:
                if turn.get("role") == "user":
                    prompt += f"<start_of_turn>user\n{turn['content']}<end_of_turn>\n"
                elif turn.get("role") == "assistant":
                    prompt += f"<start_of_turn>model\n{turn['content']}<end_of_turn>\n"
        prompt += f"<start_of_turn>user\n{message}<end_of_turn>\n<start_of_turn>model\n"

        # Tokenize
        inputs = self._tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=settings.TOP_P,  # from env
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )

        # Decode full output
        generated_full = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the model's response
        if "<start_of_turn>model\n" in generated_full:
            response = generated_full.split("<start_of_turn>model\n")[-1].strip()
        else:
            # Fallback: remove prompt part
            prompt_text = self._tokenizer.decode(
                inputs["input_ids"][0], skip_special_tokens=True
            )
            response = generated_full[len(prompt_text) :].strip()

        # Simulate streaming word by word
        words = response.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.02)  # small delay for realism

    async def health_check(self) -> bool:
        """Quick health check by generating a short test response."""
        try:
            self._load_model()
            test_gen = self.generate("سلام", max_tokens=5)
            async for _ in test_gen:
                break
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Singleton instance of the model service
fine_tuned_service = FineTunedModelService()


# ----------------------------------------------------------------------
# 3. FineTunedProvider (wraps fine_tuned_service to implement AIProvider)
# ----------------------------------------------------------------------
class FineTunedProvider(AIProvider):
    def __init__(self):
        self._service = fine_tuned_service

    async def generate_response(
        self,
        message: str,
        history: List[dict] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response from fine-tuned Gemma 2 model."""
        async for chunk in self._service.generate(
            message=message,
            history=history or [],
            system_prompt=system_prompt,
            temperature=settings.TEMPERATURE,  # from env
            max_tokens=settings.MAX_TOKENS,    # from env
        ):
            yield chunk

    async def health_check(self) -> bool:
        return await self._service.health_check()


# ----------------------------------------------------------------------
# 4. MockProvider (Fallback when no model is available)
# ----------------------------------------------------------------------
class MockProvider(AIProvider):
    """Mock provider for demo or fallback scenarios."""

    async def generate_response(
        self,
        message: str,
        history: List[dict] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        import random

        responses = [
            "سلام！ چطور میتونم کمکتون کنم؟ ",
            "متوجه شدم. لطفاً بیشتر توضیح بدید. ",
            "بر اساس علائمی که گفتید، پیشنهاد میکنم به پزشک مراجعه کنید. ",
        ]
        response_text = random.choice(responses)
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.03)

    async def health_check(self) -> bool:
        return True


# ----------------------------------------------------------------------
# 5. Factory to get the appropriate provider
# ----------------------------------------------------------------------
class AIProviderFactory:
    _instance = None

    @classmethod
    def get_provider(cls) -> AIProvider:
        if cls._instance is None:
            # Always use fine-tuned provider; fallback to Mock if needed
            try:
                cls._instance = FineTunedProvider()
                # Optionally test health check; if fails, fallback to Mock
                # (you can decide to raise or log)
            except Exception as e:
                logger.error(f"Could not initialize FineTunedProvider: {e}. Using MockProvider.")
                cls._instance = MockProvider()
        return cls._instance