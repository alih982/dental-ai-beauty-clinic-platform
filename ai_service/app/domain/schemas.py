"""Pydantic models for request/response validation"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat endpoint"""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Creativity level")
    enable_rag: bool = Field(False, description="Enable Retrieval-Augmented Generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "سردرد شدید دارم و تب کرده‌ام",
                "conversation_id": "conv-123",
                "temperature": 0.7
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    success: bool
    message: str
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "بر اساس علائم شما ممکن است...",
                "conversation_id": "conv-123",
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class MedicalSummaryRequest(BaseModel):
    """Request for medical summary"""
    symptoms: str = Field(..., min_length=3, description="Patient symptoms")
    patient_history: Optional[str] = Field(None, description="Medical history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": "سردرد، تب، گلودرد",
                "patient_history": "سابقه دیابت و فشار خون"
            }
        }


class SpecialistSuggestionRequest(BaseModel):
    """Request for specialist suggestions"""
    symptoms: str = Field(..., min_length=3, description="Patient symptoms")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": "درد مفاصل و تورم"
            }
        }


class SpecialistSuggestionResponse(BaseModel):
    """Response with specialist suggestions"""
    success: bool
    specialists: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "specialists": ["روماتولوژی", "ارتوپدی", "طب فیزیکی"]
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    model: str
    model_available: bool
    timestamp: datetime = Field(default_factory=datetime.now)
