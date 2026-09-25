import json
import logging
from typing import Dict, Any, List, Optional
from apps.ai_orchestrator.infrastructure.factory import AIFactory
from apps.ai_orchestrator.domain.ports import Prompt
from config.env_config import config

logger = logging.getLogger(__name__)

class AIService:
    """
    Core AI Service for DoctorHub.
    Orchestrates LLM calls for chat, triage, and decision support.
    """
    
    @staticmethod
    def get_manager():
        try:
            return AIFactory.create(
                provider_type=config.AI_PROVIDER,
                host=config.OLLAMA_HOST,
                api_key=config.OPENAI_API_KEY,
                endpoint=f"{config.AI_SERVICE_URL}/api/v1/chat"
            )
        except Exception as e:
            logger.error(f"Failed to create AI Manager: {e}")
            return None

    @classmethod
    async def generate_response(cls, message: str, user) -> str:
        """Simple chat response (Legacy compatibility)"""
        manager = cls.get_manager()
        if not manager:
            return "AI Service is currently unavailable. Please try again later."

        prompt = Prompt()
        prompt.text = message
        prompt.system_prompt = (
            "You are DoctorHub AI, a senior cardiologist. "
            "Focus on cardiovascular health. Be professional, concise, and empathetic."
        )
        
        try:
            completion = await manager.generate_response(prompt)
            return completion.content
        except Exception as e:
            logger.error(f"AI Generation failed: {e}")
            return "I apologize, but I'm having trouble connecting to my knowledge base right now."

    @classmethod
    async def stream_chat(cls, message: str, user, enable_rag: bool = False):
        """Yields chunks of the AI response."""
        manager = cls.get_manager()
        if not manager:
            yield "AI Service unavailable."
            return

        prompt = Prompt()
        prompt.text = message
        prompt.system_prompt = (
            "You are DoctorHub AI, a senior cardiologist. "
            "Focus on cardiovascular health. Be extremely concise and professional."
        )
        prompt.parameters = {"enable_rag": enable_rag}
        
        try:
            async for chunk in manager.stream_response(prompt):
                yield chunk
        except Exception as e:
            logger.error(f"AI Streaming failed: {e}")
            yield "Connection error during generation."

    @classmethod
    async def analyze_clinical_context(cls, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyzes the chat history to make 'Decisions'.
        Decisions include: Recommend Specialty, Suggest Prescription, Trigger Checkout.
        """
        manager = cls.get_manager()
        if not manager:
            return {"summary": "AI Service unavailable", "decisions": []}
        
        # Build context from history
        history_str = "\n".join([f"{m['sender']}: {m['content']}" for m in conversation_history])
        
        prompt_text = f"""
        Analyze the following consultation history and determine if any clinical decisions should be made.
        History:
        {history_str}
        
        Output valid JSON with the following keys:
        - "summary": A brief clinical summary.
        - "decisions": List of decision objects with "type" and "payload".
        Types: "RECOMMEND_SPECIALTY", "SUGGEST_PRESCRIPTION", "FINISH_SESSION".
        
        If no decision is needed, leave "decisions" empty.
        """
        
        prompt = Prompt()
        prompt.text = prompt_text
        prompt.system_prompt = "You are a clinical decision support system. Output ONLY valid JSON."
        
        try:
            completion = await manager.generate_response(prompt)
        except Exception as e:
            logger.error(f"AI Analysis failed: {e}")
            return {"summary": "Error analyzing context", "decisions": []}
        
        try:
            # Simple JSON extraction (refined in production)
            start = completion.content.find('{')
            end = completion.content.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(completion.content[start:end])
            return {"summary": "No decisions", "decisions": []}
        except Exception as e:
            logger.error(f"Failed to parse AI decision: {e}")
            return {"summary": "Error parsing decisions", "decisions": []}
