# """
# WebSocket endpoint for real-time AI chat with fine-tuned models
# """
# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
# from fastapi.responses import JSONResponse
# from typing import Dict, Any
# import json
# import logging

# from app.services.ai_service import ai_business_service
# from app.config import settings
# from app.utils.security import scrub_phi
# from app.domain.schemas import ChatRequest

# router = APIRouter()
# logger = logging.getLogger(__name__)


# class ConnectionManager:
#     """Manager for WebSocket connections"""
#     active_connections: Dict[str, WebSocket] = {}
    
#     async def connect(self, client_id: str, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections[client_id] = websocket
#         logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
#     def disconnect(self, client_id: str):
#         if client_id in self.active_connections:
#             del self.active_connections[client_id]
#         logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
#     async def send_message(self, message: str, client_id: str):
#         if client_id in self.active_connections:
#             await self.active_connections[client_id].send_text(message)
    
#     async def send_json(self, data: Dict, client_id: str):
#         if client_id in self.active_connections:
#             await self.active_connections[client_id].send_json(data)


# manager = ConnectionManager()


# @router.websocket("/ws/ai-chat")
# async def websocket_ai_chat(websocket: WebSocket):
#     """
#     WebSocket endpoint for real-time AI chat using fine-tuned models.
    
#     Protocol:
#     - Client sends: {"type": "chat", "message": "...", "enable_rag": false, "history": [...]}
#     - Server sends: {"type": "chunk", "content": "..."} (streaming)
#     - Server sends: {"type": "complete", "full_content": "..."} (done)
#     - Server sends: {"type": "error", "content": "..."}
#     """
#     client_id = None
#     try:
#         # Accept connection
#         await websocket.accept()
        
#         # Get client identifier
#         client_id = f"client_{id(websocket)}"
#         manager.active_connections[client_id] = websocket
        
#         logger.info(f"WebSocket AI Chat: Client {client_id} connected")
        
#         # Send welcome message
#         await websocket.send_json({
#             "type": "system",
#             "content": "Connected to AI Chat Service",
#             "model": "fine_tuned_gemma" if settings.USE_FINE_TUNED else "gemma2",
#             "use_rag": settings.EMBEDDING_MODEL is not None
#         })
        
#         # Message loop
#         while True:
#             data = await websocket.receive_text()
            
#             try:
#                 message_data = json.loads(data)
#             except json.JSONDecodeError:
#                 await websocket.send_json({
#                     "type": "error",
#                     "content": "Invalid JSON format"
#                 })
#                 continue
            
#             message_type = message_data.get("type", "chat")
            
#             if message_type == "chat":
#                 await handle_chat_message(websocket, message_data, client_id)
            
#             elif message_type == "ping":
#                 await websocket.send_json({"type": "pong"})
            
#             elif message_type == "history":
#                 # Get conversation history
#                 history = message_data.get("history", [])
#                 await websocket.send_json({
#                     "type": "history_response",
#                     "history": history
#                 })
            
#             else:
#                 await websocket.send_json({
#                     "type": "error",
#                     "content": f"Unknown message type: {message_type}"
#                 })
    
#     except WebSocketDisconnect:
#         logger.info(f"WebSocket disconnected: {client_id}")
#     except Exception as e:
#         logger.error(f"WebSocket error: {str(e)}", exc_info=True)
#         try:
#             await websocket.send_json({
#                 "type": "error",
#                 "content": f"Server error: {str(e)}"
#             })
#         except:
#             pass
#     finally:
#         if client_id:
#             manager.disconnect(client_id)


# async def handle_chat_message(websocket: WebSocket, data: Dict, client_id: str):
#     """Handle incoming chat message"""
#     message = data.get("message", "")
#     enable_rag = data.get("enable_rag", False)
#     history = data.get("history", [])
    
#     if not message:
#         await websocket.send_json({
#             "type": "error",
#             "content": "Empty message"
#         })
#         return
    
#     # PHI Scrubbing for security
#     clean_message = scrub_phi(message) if settings.ENABLE_PHI_SCRUBBING else message
    
#     # Build chat request
#     request = ChatRequest(
#         message=clean_message,
#         enable_rag=enable_rag,
#         history=history
#     )
    
#     # Stream response
#     full_content = ""
    
#     try:
#         async for chunk in ai_business_service.get_chat_stream(request, db=None):
#             full_content += chunk
#             await websocket.send_json({
#                 "type": "chunk",
#                 "content": chunk,
#                 "done": False
#             })
        
#         # Send completion
#         await websocket.send_json({
#             "type": "complete",
#             "full_content": full_content,
#             "done": True
#         })
        
#     except Exception as e:
#         logger.error(f"Chat error: {str(e)}", exc_info=True)
#         await websocket.send_json({
#             "type": "error",
#             "content": f"AI processing error: {str(e)}"
#         })


# @router.get("/ws/connections")
# async def get_active_connections():
#     """Get count of active WebSocket connections"""
#     return {
#         "active_connections": len(manager.active_connections),
#         "clients": list(manager.active_connections.keys())
#     }

"""
WebSocket endpoint for real-time chat with local fine-tuned model.
No database, no RAG, no Ollama.
"""
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from app.core.provider import AIProviderFactory

logger = logging.getLogger(__name__)

# Get the AI provider (FineTunedProvider -> local model)
provider = AIProviderFactory.get_provider()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected: {websocket.client}")

    async def send_message(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            logger.warning(f"Failed to send message: {e}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            await self.send_message(connection, message)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                history = message_data.get("history", [])   # List of {"role": "user"/"assistant", "content": "..."}
                system_prompt = message_data.get("system_prompt", None)
            except json.JSONDecodeError:
                user_message = data
                history = []
                system_prompt = None

            logger.info(f"Received message: {user_message[:50]}...")

            # Send acknowledgment
            await manager.send_message(websocket, {
                "type": "ai_response_chunk",
                "content": "",
                "done": False
            })

            # Stream response from local model
            full_response = ""
            try:
                async for chunk in provider.generate_response(
                    message=user_message,
                    history=history,
                    system_prompt=system_prompt
                ):
                    full_response += chunk
                    await manager.send_message(websocket, {
                        "type": "ai_response_chunk",
                        "content": chunk,
                        "done": False
                    })

                # Send completion message
                await manager.send_message(websocket, {
                    "type": "ai_response_complete",
                    "content": full_response,
                    "done": True
                })
                logger.info(f"Response sent, length: {len(full_response)} chars")

            except Exception as e:
                logger.error(f"Error generating response: {e}", exc_info=True)
                await manager.send_message(websocket, {
                    "type": "error",
                    "content": "خطا در تولید پاسخ",
                    "done": True
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        manager.disconnect(websocket)


# Include router in main.py already done; ensure this router is added in main.py