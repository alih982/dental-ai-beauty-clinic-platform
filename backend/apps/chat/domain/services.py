"""Chat service using new AI orchestrator"""
from apps.ai_orchestrator.application.services import get_ai_service


class ChatService:
    """Service for handling chat interactions with AI"""
    
    def __init__(self):
        """Initialize chat service with AI orchestrator"""
        self.ai_service = get_ai_service()
    
    async def generate_reply(self, message: str, system_prompt: str = None) -> str:
        """
        Generate a complete response from AI.
        
        Args:
            message: User's message
            system_prompt: Optional system context
            
        Returns:
            AI generated response
        """
        response = await self.ai_service.generate_response(
            prompt=message,
            system_prompt=system_prompt
        )
        return response.content
    
    async def stream_reply(self, message: str, system_prompt: str = None):
        """
        Stream response from AI.
        
        Args:
            message: User's message
            system_prompt: Optional system context
            
        Yields:
            Response chunks as they're generated
        """
        async for chunk in self.ai_service.stream_response(
            prompt=message,
            system_prompt=system_prompt
        ):
            yield chunk
