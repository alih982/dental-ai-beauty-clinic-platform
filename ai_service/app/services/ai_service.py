"""
AI Service Layer - Business logic for medical assistant
"""
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.orm import Session
import json
from app.domain.schemas import ChatRequest
from app.core.provider import AIProviderFactory
from app.api.v1.control import get_runtime_system_prompt

from app.utils.security import scrub_phi
from app.services.rag_service import rag_service
from app.config import settings

# Try to import fine-tuned service, but don't fail if not available
try:
    from app.services.finetuned_inference import fine_tuned_service
    FINE_TUNED_AVAILABLE = True
except ImportError:
    FINE_TUNED_AVAILABLE = False
    fine_tuned_service = None

logger = logging.getLogger(__name__)

class AIBusinessService:
    def __init__(self):
        pass  # Provider is fetched per request or cached globally

    @property
    def provider(self):
        return AIProviderFactory.get_provider()

    async def get_chat_stream(self, request: ChatRequest, db: Session) -> AsyncGenerator[str, None]:
        """
        Generate streaming chat response using the configured provider.
        Supports both fine-tuned models and standard Ollama provider.
        """
        # PHI Scrubbing for security compliance
        clean_message = scrub_phi(request.message) if settings.ENABLE_PHI_SCRUBBING else request.message
        
        system_prompt = get_runtime_system_prompt()
        
        # RAG Logic Integration
        if request.enable_rag:
            logger.info(f"RAG Mode Enabled for request: {request.message[:50]}...")
            async for chunk in rag_service.query_stream(db, clean_message):
                yield chunk
            return

        # Use fine-tuned model if enabled and available
        if settings.USE_FINE_TUNED and FINE_TUNED_AVAILABLE and fine_tuned_service:
            logger.info("Using fine-tuned model for inference")
            history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.history
            ] if request.history else []
            
            try:
                async for chunk in fine_tuned_service.generate(
                    message=clean_message,
                    history=history,
                    system_prompt=system_prompt,
                    temperature=request.temperature or settings.TEMPERATURE,
                    max_tokens=settings.MAX_TOKENS,
                    model_name=settings.DEFAULT_MODEL_NAME
                ):
                    yield chunk
                return
            except Exception as e:
                logger.error(f"Fine-tuned model error: {e}. Falling back to standard provider.")

        # Fallback to standard flow (Ollama)
        history = [
            {"role": msg.role, "content": msg.content} 
            for msg in request.history
        ] if request.history else []

        async for chunk in self.provider.generate_response(
            message=clean_message,
            history=history,
            system_prompt=system_prompt
        ):
            yield chunk

    async def get_chat_response(self, request: ChatRequest, db: Session) -> str:
        """Get full response (non-streaming)."""
        response_parts = []
        async for chunk in self.get_chat_stream(request, db):
            response_parts.append(chunk)
        return "".join(response_parts)

    async def get_medical_summary(self, symptoms: str, patient_history: str = None) -> str:
        """Specialized prompt for medical summary."""
        system_prompt = "You are a medical summarization assistant. Summarize the symptoms and history concisely."
        prompt = f"Symptoms: {symptoms}\nHistory: {patient_history or 'None'}"
        
        response_parts = []
        
        if settings.USE_FINE_TUNED and FINE_TUNED_AVAILABLE and fine_tuned_service:
            try:
                async for chunk in fine_tuned_service.generate(
                    prompt=prompt, 
                    system_prompt=system_prompt,
                    model_name=settings.DEFAULT_MODEL_NAME
                ):
                    response_parts.append(chunk)
                return "".join(response_parts)
            except Exception as e:
                logger.error(f"Fine-tuned model error in summary: {e}")
        
        async for chunk in self.provider.generate_response(message=prompt, system_prompt=system_prompt):
            response_parts.append(chunk)
        return "".join(response_parts)

    async def get_specialist_suggestions(self, symptoms: str) -> list:
        """Suggest specialists based on symptoms."""
        system_prompt = "You are a medical triage assistant. Suggest 3 specialist types for these symptoms. Return ONLY a JSON array of strings."
        
        response_parts = []
        
        if settings.USE_FINE_TUNED and FINE_TUNED_AVAILABLE and fine_tuned_service:
            try:
                async for chunk in fine_tuned_service.generate(
                    message=symptoms, 
                    system_prompt=system_prompt,
                    model_name=settings.DEFAULT_MODEL_NAME
                ):
                    response_parts.append(chunk)
                
                full_text = "".join(response_parts)
                try:
                    start = full_text.find('[')
                    end = full_text.rfind(']') + 1
                    if start != -1 and end != 0:
                        return json.loads(full_text[start:end])
                    return ["General Practitioner"]
                except:
                    return ["General Practitioner"]
            except Exception as e:
                logger.error(f"Fine-tuned model error in suggestions: {e}")
        
        async for chunk in self.provider.generate_response(message=symptoms, system_prompt=system_prompt):
            response_parts.append(chunk)
        
        full_text = "".join(response_parts)
        try:
            start = full_text.find('[')
            end = full_text.rfind(']') + 1
            if start != -1 and end != 0:
                return json.loads(full_text[start:end])
            return ["General Practitioner"]
        except:
            return ["General Practitioner"]

ai_business_service = AIBusinessService()

