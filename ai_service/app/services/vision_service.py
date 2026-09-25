"""
AI Vision Service - Image Analysis for Skin Care Products
Celery is OPTIONAL - falls back to synchronous processing if not available
"""

import io
import base64
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import numpy and PIL, but make them optional
try:
    import numpy as np
    from PIL import Image
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.warning("numpy or Pillow not available - vision service will use mock mode")

# Try Celery, but make it optional
try:
    from celery import Celery
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    logger.warning("Celery not available - using synchronous processing only")

# Celery Configuration - only if available
if HAS_CELERY:
    import os
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis.runflare.local:6379')
    
    try:
        celery_app = Celery(
            'ai_vision',
            broker=f'{REDIS_URL}/1',
            backend=f'{REDIS_URL}/2'
        )
        
        celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=300,
            task_soft_time_limit=240,
        )
    except Exception as e:
        logger.warning(f"Celery init failed: {e}")
        HAS_CELERY = False
        celery_app = None
else:
    celery_app = None


class ImageAnalysisRequest:
    image_data: str
    analysis_type: str = "skin_care"

class ProductRecommendation:
    name: str
    category: str
    description: str
    confidence: float

class ImageAnalysisResponse:
    success: bool
    skin_type: Optional[str] = None
    concerns: Optional[List[str]] = None
    products: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None


# Mock skin care product database
SKIN_CARE_PRODUCTS = {
    "dry": [
        {"name": "Hydrating Serum", "category": "Serum", "description": "مرطوب‌کننده عمیق با هیالورونیک اسید", "confidence": 0.95},
        {"name": "Rich Moisturizer", "category": "Moisturizer", "description": "کرم مرطوب‌کننده غنی برای پوست خشک", "confidence": 0.92},
        {"name": "Cleansing Milk", "category": "Cleanser", "description": "شوینده ملایم بدون خشک کردن پوست", "confidence": 0.88},
    ],
    "oily": [
        {"name": "Gel Cleanser", "category": "Cleanser", "description": "ژل شوینده کنترل‌کننده چربی", "confidence": 0.94},
        {"name": "Salicylic Acid Toner", "category": "Toner", "description": "تونر ضد جوش با سالیسیلیک اسید", "confidence": 0.91},
        {"name": "Lightweight Gel Moisturizer", "category": "Moisturizer", "description": "مرطوب‌کننده سبک بدون چربی", "confidence": 0.89},
    ],
    "sensitive": [
        {"name": "Gentle Cleanser", "category": "Cleanser", "description": "شوینده بسیار ملایم hypoallergenic", "confidence": 0.96},
        {"name": "Calming Serum", "category": "Serum", "description": "سرم آرام‌بخش با عصاره بابونه", "confidence": 0.93},
        {"name": "Mineral Sunscreen", "category": "Sunscreen", "description": "ضدآفتاب معدنی بدون حساسیت", "confidence": 0.95},
    ],
    "combination": [
        {"name": "Balancing Cleanser", "category": "Cleanser", "description": "شوینده متعادل‌کننده پوست", "confidence": 0.90},
        {"name": "Dual Action Moisturizer", "category": "Moisturizer", "description": "مرطوب‌کننده دوگانه برای پوست ترکیبی", "confidence": 0.87},
        {"name": "Exfoliating Toner", "category": "Toner", "description": "تونر لایه‌بردار ملایم", "confidence": 0.85},
    ],
    "normal": [
        {"name": "Daily Cleanser", "category": "Cleanser", "description": "شوینده روزانه ملایم", "confidence": 0.92},
        {"name": "Vitamin C Serum", "category": "Serum", "description": "سرم ویتامین C روشن‌کننده", "confidence": 0.90},
        {"name": "Daily Moisturizer", "category": "Moisturizer", "description": "مرطوب‌کننده روزانه", "confidence": 0.88},
    ],
}


def preprocess_image(image_data: str):
    """Convert base64 image to numpy array for processing."""
    if not HAS_NUMPY:
        logger.warning("numpy not available - using mock preprocessing")
        return None
    
    logger.info("Preprocessing image to numpy array...")
    
    if "data:image" in image_data:
        image_data = image_data.split(",")[1]
    
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image = image.resize((224, 224))
    img_array = np.array(image, dtype=np.float32)
    img_array = img_array / 255.0
    
    logger.info(f"Image converted to numpy array with shape: {img_array.shape}")
    return img_array


def analyze_skin_type(image_array) -> str:
    """Analyze skin type from numpy array image data."""
    if image_array is None:
        return "normal"  # Default fallback
    
    avg_brightness = float(np.mean(image_array))
    red_channel = image_array[:, :, 0]
    green_channel = image_array[:, :, 1]
    blue_channel = image_array[:, :, 2]
    redness = float(np.mean(red_channel - (green_channel + blue_channel) / 2))
    variance = float(np.var(image_array))
    
    if avg_brightness < 0.4:
        if redness > 0.05:
            return "sensitive"
        return "dry"
    elif avg_brightness > 0.7:
        return "oily"
    elif redness > 0.08:
        return "sensitive"
    elif variance > 0.05:
        return "combination"
    else:
        return "normal"


def detect_skin_concerns(image_array) -> List[str]:
    """Detect skin concerns from numpy array image data."""
    if image_array is None:
        return ["پوست سالم"]
    
    concerns = []
    avg_brightness = float(np.mean(image_array))
    brightness_std = float(np.std(image_array))
    red_channel = image_array[:, :, 0]
    green_channel = image_array[:, :, 1]
    blue_channel = image_array[:, :, 2]
    redness = float(np.mean(red_channel - (green_channel + blue_channel) / 2))
    dark_regions = float(np.sum(image_array < 0.3) / image_array.size)
    bright_regions = float(np.sum(image_array > 0.8) / image_array.size)
    gradient_x = np.gradient(image_array[:, :, 0], axis=0)
    gradient_y = np.gradient(image_array[:, :, 1], axis=1)
    texture_score = float(np.mean(np.abs(gradient_x) + np.abs(gradient_y)))
    
    if redness > 0.05:
        concerns.append("قرمزی و تحریک پوست")
    if avg_brightness < 0.5:
        concerns.append("کدری پوست")
    if dark_regions > 0.1:
        concerns.append("لکه‌های تیره")
    if bright_regions > 0.15:
        concerns.append("آسیب نور خورشید")
    if avg_brightness > 0.7:
        concerns.append("چربی بیش از حد")
    if avg_brightness < 0.35:
        concerns.append("خشکی پوست")
    if texture_score > 0.1:
        concerns.append("بافت ناهموار")
    if brightness_std > 0.15:
        concerns.append("تغییرات رنگدانه")
    
    if not concerns:
        concerns.append("پوست سالم")
    
    return concerns


def _analyze_image_core(image_data: str, analysis_type: str = "skin_care") -> Dict[str, Any]:
    """Core image analysis logic (synchronous)."""
    try:
        image_array = preprocess_image(image_data)
        skin_type = analyze_skin_type(image_array)
        concerns = detect_skin_concerns(image_array)
        products = SKIN_CARE_PRODUCTS.get(skin_type, SKIN_CARE_PRODUCTS["normal"])
        
        return {
            "success": True,
            "skin_type": skin_type,
            "concerns": concerns,
            "products": products,
            "message": "تحلیل با موفقیت انجام شد"
        }
    except Exception as e:
        logger.error(f"Error in image analysis: {str(e)}")
        return {
            "success": False,
            "message": f"خطا در تحلیل تصویر: {str(e)}"
        }


# Celery task wrapper (only if Celery is available)
if HAS_CELERY and celery_app:
    @celery_app.task(bind=True, name='ai_vision.analyze_image')
    def analyze_image_task(self, image_data: str, analysis_type: str = "skin_care"):
        """Celery task for async image analysis."""
        logger.info(f"Starting image analysis task (ID: {self.request.id})")
        return _analyze_image_core(image_data, analysis_type)
else:
    # Stub task function
    def analyze_image_task(image_data: str, analysis_type: str = "skin_care"):
        """Synchronous fallback when Celery is not available."""
        logger.warning("Celery not available - running synchronously")
        return _analyze_image_core(image_data, analysis_type)


def analyze_image_sync(image_data: str, analysis_type: str = "skin_care") -> dict:
    """Synchronous image analysis - always works regardless of Celery."""
    return _analyze_image_core(image_data, analysis_type)


# FastAPI endpoint helpers
async def analyze_image_endpoint(image_data: str, analysis_type: str = "skin_care"):
    """Submit image analysis - uses Celery if available, otherwise sync."""
    if HAS_CELERY and celery_app:
        task = analyze_image_task.delay(image_data, analysis_type)
        return {"task_id": task.id, "status": "pending"}
    else:
        result = analyze_image_sync(image_data, analysis_type)
        return {"result": result, "status": "completed"}


async def get_analysis_result(task_id: str):
    """Get analysis result - Celery or direct."""
    if HAS_CELERY and celery_app:
        from celery.result import AsyncResult
        result = AsyncResult(task_id, app=celery_app)
        if result.ready():
            return result.get()
        return {"status": "processing", "task_id": task_id}
    else:
        return {"status": "not_available", "message": "Celery not configured"}

