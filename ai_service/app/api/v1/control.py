from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AIConfig(BaseModel):
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    use_fine_tuned: Optional[bool] = None

# Runtime configuration
runtime_config = {
    "system_prompt": (
        "شما DoctorHub AI، دستیار هوشمند پزشکی هستید. "
        "شما باید به سوالات کاربران در مورد مسائل پزشکی پاسخ دهید. "
        "همیشه تاکید کنید که این اطلاعات جنبه آموزشی دارد و جایگزین مشاوره پزشکی نیست. "
        "در صورت نیاز به کاربر توصیه کنید که با پزشک مشورت کند. "
        "پاسخ‌های خود را کوتاه، حرفه‌ای و با لحنی دوستانه ارائه دهید."
    ),
    "temperature": 0.7,
    "use_fine_tuned": True
}

@router.post("/config")
async def update_config(config: AIConfig):
    """Update runtime AI configuration."""
    if config.system_prompt is not None:
        runtime_config["system_prompt"] = config.system_prompt
    if config.temperature is not None:
        runtime_config["temperature"] = config.temperature
    if config.use_fine_tuned is not None:
        runtime_config["use_fine_tuned"] = config.use_fine_tuned
    
    return {"status": "success", "config": runtime_config}

@router.get("/config")
async def get_config():
    """Get current runtime AI configuration."""
    return runtime_config

def get_runtime_system_prompt():
    return runtime_config.get("system_prompt", "شما یک دستیار پزشکی هوشمند هستید.")

def get_runtime_temperature():
    return runtime_config.get("temperature", 0.7)

def is_fine_tuned_enabled():
    return runtime_config.get("use_fine_tuned", True)

