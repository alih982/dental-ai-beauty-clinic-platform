"""
WhatsApp Notification Service via Meta Business API

Handles sending WhatsApp messages for appointment reminders,
prescription notifications, and health alerts.

Status: Inactive (ready for configuration)
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import aiohttp
import logging
from django.conf import settings


logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WhatsApp message types"""
    APPOINTMENT_REMINDER = "appointment_reminder"
    PRESCRIPTION_READY = "prescription_ready"
    LAB_RESULTS = "lab_results"
    GENERAL_NOTIFICATION = "general"


@dataclass
class WhatsAppMessage:
    """WhatsApp message entity"""
    phone_number: str  # Format: +989123456789
    message_type: MessageType
    content: str
    template_name: Optional[str] = None
    template_params: Dict[str, Any] = None
    

class WhatsAppService:
    """
    WhatsApp Business API integration service.
    
    Configuration required in settings.py:
    - WHATSAPP_ACCESS_TOKEN
    - WHATSAPP_PHONE_NUMBER_ID
    - WHATSAPP_BUSINESS_ACCOUNT_ID
    
    To activate:
    1. Create Meta Business account
    2. Set up WhatsApp Business API
    3. Get access token
    4. Configure environment variables
    """
    
    def __init__(self):
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        self.api_version = getattr(settings, 'WHATSAPP_API_VERSION', 'v18.0')
        self.base_url = f"http://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        self.is_active = bool(self.access_token and self.phone_number_id)
    
    async def send_message(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Send WhatsApp message.
        
        Args:
            message: WhatsApp message to send
            
        Returns:
            Response from Meta API
            
        Raises:
            Exception: If service is not configured or send fails
        """
        if not self.is_active:
            logger.warning("WhatsApp service is not configured. Message not sent.")
            return {
                "status": "skipped",
                "reason": "service_not_configured",
                "message": "Configure WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID to activate"
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Use template if specified, otherwise send text
        if message.template_name:
            payload = self._build_template_payload(message)
        else:
            payload = self._build_text_payload(message)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                ) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        logger.info(f"WhatsApp message sent to {message.phone_number}")
                        return {
                            "status": "sent",
                            "message_id": data.get("messages", [{}])[0].get("id"),
                            "response": data
                        }
                    else:
                        logger.error(f"WhatsApp send failed: {data}")
                        return {
                            "status": "failed",
                            "error": data.get("error", {}).get("message", "Unknown error")
                        }
                        
        except Exception as e:
            logger.error(f"WhatsApp error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_appointment_reminder(
        self,
        phone_number: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str
    ) -> Dict[str, Any]:
        """
        Send appointment reminder.
        
        Args:
            phone_number: Patient's phone number
            doctor_name: Doctor's name
            appointment_date: Appointment date
            appointment_time: Appointment time
            
        Returns:
            Send result
        """
        message = WhatsAppMessage(
            phone_number=phone_number,
            message_type=MessageType.APPOINTMENT_REMINDER,
            content=f"یادآوری نوبت\n\nدکتر: {doctor_name}\nتاریخ: {appointment_date}\nساعت: {appointment_time}\n\nلطفاً در زمان مقرر حضور یابید.",
            template_name="appointment_reminder",  # Pre-approved template
            template_params={
                "doctor_name": doctor_name,
                "date": appointment_date,
                "time": appointment_time
            }
        )
        
        return await self.send_message(message)
    
    async def send_prescription_notification(
        self,
        phone_number: str,
        prescription_id: str,
        download_link: str
    ) -> Dict[str, Any]:
        """Send prescription ready notification"""
        message = WhatsAppMessage(
            phone_number=phone_number,
            message_type=MessageType.PRESCRIPTION_READY,
            content=f"نسخه الکترونیک شما آماده است!\n\nشماره نسخه: {prescription_id}\n\nلینک دانلود:\n{download_link}"
        )
        
        return await self.send_message(message)
    
    def _build_text_payload(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Build payload for text message"""
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.phone_number,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message.content
            }
        }
    
    def _build_template_payload(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Build payload for template message"""
        components = []
        
        if message.template_params:
            # Build parameters for template
            parameters = [
                {"type": "text", "text": value}
                for value in message.template_params.values()
            ]
            
            components.append({
                "type": "body",
                "parameters": parameters
            })
        
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.phone_number,
            "type": "template",
            "template": {
                "name": message.template_name,
                "language": {"code": "fa"},  # Persian
                "components": components
            }
        }
    
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check message delivery status.
        
        Args:
            message_id: Message ID from send response
            
        Returns:
            Delivery status
        """
        if not self.is_active:
            return {"status": "service_not_configured"}
        
        # Implement status checking via webhooks or API
        # This is typically done via webhook callbacks
        return {"status": "pending", "note": "Use webhooks for real-time status"}


# Singleton instance
whatsapp_service = WhatsAppService()
