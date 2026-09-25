"""
AI Vision API - FastAPI endpoints for image analysis
Works WITHOUT Celery - synchronous processing only
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json
import logging

from app.services.vision_service import (
    analyze_image_sync,
    SKIN_CARE_PRODUCTS,
)

logger = logging.getLogger(__name__)

router = APIRouter()

class ImageAnalysisRequest(BaseModel):
    image_data: str
    analysis_type: str = "skin_care"


@router.post("/analyze-image")
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze image synchronously (no Celery needed)
    """
    result = analyze_image_sync(request.image_data, request.analysis_type)
    return {
        "success": result.get("success"),
        "data": result,
        "message": result.get("message")
    }


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected to vision WebSocket")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected from vision WebSocket")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        for client_id in list(self.active_connections.keys()):
            await self.send_message(client_id, message)


manager = ConnectionManager()


@router.websocket("/ws/vision")
async def websocket_vision(websocket: WebSocket):
    """
    WebSocket endpoint for real-time image analysis (synchronous, no Celery)
    """
    import uuid
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    try:
        await manager.send_message(client_id, {
            "type": "connected",
            "message": "به سیستم تحلیل پوست متصل شدید",
            "client_id": client_id
        })
        
        logger.info(f"Vision WebSocket session started for client {client_id}")
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "image":
                image_data = message.get("data", "")
                
                if not image_data:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": "تصویر دریافت نشد"
                    })
                    continue
                
                await manager.send_message(client_id, {
                    "type": "status",
                    "message": "در حال تحلیل پوست..."
                })
                
                try:
                    logger.info(f"Processing image for client {client_id}")
                    result = analyze_image_sync(image_data, "skin_care")
                    
                    if result.get("success"):
                        await manager.send_message(client_id, {
                            "type": "result",
                            "success": True,
                            "skin_type": result.get("skin_type"),
                            "skin_type_fa": get_skin_type_fa(result.get("skin_type")),
                            "concerns": result.get("concerns", []),
                            "products": [
                                {
                                    "name": p["name"],
                                    "name_fa": get_product_name_fa(p["name"]),
                                    "category": p["category"],
                                    "description": p["description"],
                                    "confidence": p["confidence"]
                                }
                                for p in result.get("products", [])
                            ],
                            "message": result.get("message")
                        })
                        logger.info(f"Image analysis completed for client {client_id}")
                    else:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": result.get("message", "خطا در تحلیل تصویر")
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing image: {str(e)}")
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": f"خطا در پردازش تصویر: {str(e)}"
                    })
            
            elif message.get("type") == "ping":
                await manager.send_message(client_id, {"type": "pong"})
            
            elif message.get("type") == "health":
                await manager.send_message(client_id, {
                    "type": "health",
                    "status": "ok",
                    "service": "vision"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(client_id)


def get_skin_type_fa(skin_type: str) -> str:
    translations = {
        "dry": "پوست خشک",
        "oily": "پوست چرب",
        "sensitive": "پوست حساس",
        "combination": "پوست ترکیبی",
        "normal": "پوست معمولی"
    }
    return translations.get(skin_type, skin_type)


def get_product_name_fa(name: str) -> str:
    translations = {
        "Hydrating Serum": "سرم آبرسان",
        "Rich Moisturizer": "کرم مرطوب‌کننده غنی",
        "Cleansing Milk": "شیر پاک‌کننده",
        "Gel Cleanser": "ژل شوینده",
        "Salicylic Acid Toner": "تونر سالیسیلیک اسید",
        "Lightweight Gel Moisturizer": "ژل مرطوب‌کننده سبک",
        "Gentle Cleanser": "پاک‌کننده ملایم",
        "Calming Serum": "سرم آرام‌بخش",
        "Mineral Sunscreen": "ضدآفتاب معدنی",
        "Balancing Cleanser": "پاک‌کننده متعادل‌کننده",
        "Dual Action Moisturizer": "مرطوب‌کننده دوگانه",
        "Exfoliating Toner": "تونر لایه‌بردار",
        "Daily Cleanser": "پاک‌کننده روزانه",
        "Vitamin C Serum": "سرم ویتامین C",
        "Daily Moisturizer": "مرطوب‌کننده روزانه"
    }
    return translations.get(name, name)


@router.get("/health")
async def vision_health():
    return {
        "status": "ok",
        "service": "vision",
        "features": [
            "skin_analysis",
            "product_recommendations",
            "websocket"
        ]
    }


@router.get("/ping")
async def vision_ping():
    return {"message": "pong"}
