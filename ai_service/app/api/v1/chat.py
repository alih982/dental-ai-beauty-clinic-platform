"""
Chat API endpoints with streaming support - No database, only local AI model
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import logging
from datetime import datetime

from app.domain.schemas import ChatRequest, ChatResponse
from app.core.provider import AIProviderFactory

router = APIRouter()
logger = logging.getLogger(__name__)

# Get the AI provider (FineTunedProvider which uses local model)
provider = AIProviderFactory.get_provider()


@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE).
    No database involved.
    """
    async def generate():
        conversation_id = request.conversation_id or f"conv-{datetime.now().timestamp()}"
        
        try:
            # Convert history from ChatRequest format to list of dicts
            history = []
            if request.history:
                for msg in request.history:
                    history.append({"role": msg.role, "content": msg.content})
            
            # Stream response from AI provider
            async for chunk in provider.generate_response(
                message=request.message,
                history=history,
                system_prompt=request.system_prompt
            ):
                data = {
                    "chunk": chunk,
                    "conversation_id": conversation_id,
                    "done": False
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            # Send done signal
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
        
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            error_data = {
                "error": str(e),
                "conversation_id": conversation_id,
                "done": True
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint - returns full response at once.
    No database involved.
    """
    try:
        conversation_id = request.conversation_id or f"conv-{datetime.now().timestamp()}"
        
        # Convert history
        history = []
        if request.history:
            for msg in request.history:
                history.append({"role": msg.role, "content": msg.content})
        
        # Collect all chunks from stream
        full_response = ""
        async for chunk in provider.generate_response(
            message=request.message,
            history=history,
            system_prompt=request.system_prompt
        ):
            full_response += chunk
        
        return ChatResponse(
            success=True,
            message=full_response,
            conversation_id=conversation_id
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))