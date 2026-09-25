"""
SMS Service - Multi-provider support
Supports: Kavenegar (Iran), Twilio (International)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging
import httpx
from enum import Enum

logger = logging.getLogger('apps.sms')


class SMSProvider(str, Enum):
    """Supported SMS providers"""
    KAVENGAR = 'kavenegar'
    TWILIO = 'twilio'


class BaseSMSProvider(ABC):
    """Abstract base class for SMS providers"""
    
    @abstractmethod
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send SMS"""
        pass
    
    @abstractmethod
    async def send_otp(
        self,
        phone_number: str,
        code: str,
        template: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send OTP code"""
        pass
    
    @abstractmethod
    async def send_bulk(
        self,
        phone_numbers: List[str],
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send bulk SMS"""
        pass


class KavenegarProvider(BaseSMSProvider):
    """
    Kavenegar SMS provider (Iranian SMS service).
    Docs: http://kavenegar.com/rest.html
    """
    
    BASE_URL = 'http://api.kavenegar.com/v1/'
    
    def __init__(self, api_key: str, sender: str = None):
        self.api_key = api_key
        self.sender = sender or '10004346'  # Default Kavenegar sender
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send SMS via Kavenegar.
        
        Args:
            phone_number: Iranian phone number (09xxxxxxxxx)
            message: SMS message text
        
        Returns:
            {
                'success': bool,
                'message_id': str,
                'cost': int
            }
        """
        try:
            url = f'{self.BASE_URL}{self.api_key}/sms/send.json'
            
            params = {
                'sender': kwargs.get('sender', self.sender),
                'receptor': phone_number,
                'message': message,
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get('return', {}).get('status') == 200:
                message_data = data['entries'][0]
                logger.info(f"SMS sent to {phone_number}: {message_data['messageid']}")
                
                return {
                    'success': True,
                    'message_id': str(message_data['messageid']),
                    'cost': message_data.get('cost', 0)
                }
            else:
                logger.error(f"Kavenegar SMS error: {data}")
                return {
                    'success': False,
                    'error': data.get('return', {}).get('message', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"SMS send error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_otp(
        self,
        phone_number: str,
        code: str,
        template: str = 'verify',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send OTP using Kavenegar template.
        
        Args:
            phone_number: Iranian phone number
            code: OTP code (4-6 digits)
            template: Template name (must be defined in Kavenegar panel)
        """
        try:
            url = f'{self.BASE_URL}{self.api_key}/verify/lookup.json'
            
            params = {
                'receptor': phone_number,
                'token': code,
                'template': template,
            }
            
            # Support for multiple tokens
            if 'token2' in kwargs:
                params['token2'] = kwargs['token2']
            if 'token3' in kwargs:
                params['token3'] = kwargs['token3']
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get('return', {}).get('status') == 200:
                logger.info(f"OTP sent to {phone_number}")
                return {
                    'success': True,
                    'message_id': str(data['entries'][0]['messageid'])
                }
            else:
                return {
                    'success': False,
                    'error': data.get('return', {}).get('message', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"OTP send error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_bulk(
        self,
        phone_numbers: List[str],
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send bulk SMS"""
        try:
            url = f'{self.BASE_URL}{self.api_key}/sms/sendarray.json'
            
            # Prepare arrays
            senders = [kwargs.get('sender', self.sender)] * len(phone_numbers)
            messages = [message] * len(phone_numbers)
            
            data = {
                'sender': senders,
                'receptor': phone_numbers,
                'message': messages,
            }
            
            response = await self.client.post(url, json=data)
            result = response.json()
            
            if result.get('return', {}).get('status') == 200:
                logger.info(f"Bulk SMS sent to {len(phone_numbers)} numbers")
                return {
                    'success': True,
                    'count': len(phone_numbers)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return', {}).get('message', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Bulk SMS error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class TwilioProvider(BaseSMSProvider):
    """
    Twilio SMS provider (International).
    Requires: pip install twilio
    """
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        from twilio.rest import Client
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            
            logger.info(f"Twilio SMS sent: {message_obj.sid}")
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'status': message_obj.status
            }
        
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_otp(
        self,
        phone_number: str,
        code: str,
        template: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send OTP via Twilio"""
        message = f"Your verification code is: {code}"
        return await self.send_sms(phone_number, message)
    
    async def send_bulk(
        self,
        phone_numbers: List[str],
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send bulk SMS via Twilio"""
        results = []
        errors = []
        
        for phone in phone_numbers:
            result = await self.send_sms(phone, message)
            if result['success']:
                results.append(result)
            else:
                errors.append({'phone': phone, 'error': result['error']})
        
        return {
            'success': len(errors) == 0,
            'sent': len(results),
            'failed': len(errors),
            'errors': errors
        }


class SMSProviderFactory:
    """Factory for creating SMS provider instances"""
    
    @staticmethod
    def create_provider(
        provider: SMSProvider,
        **config
    ) -> BaseSMSProvider:
        """Create SMS provider instance"""
        
        if provider == SMSProvider.KAVENEGAR:
            return KavenegarProvider(
                api_key=config.get('api_key'),
                sender=config.get('sender')
            )
        
        elif provider == SMSProvider.TWILIO:
            return TwilioProvider(
                account_sid=config.get('account_sid'),
                auth_token=config.get('auth_token'),
                from_number=config.get('from_number')
            )
        
        else:
            raise ValueError(f"Unsupported SMS provider: {provider}")


# Helper functions for common SMS operations

async def send_appointment_reminder(
    phone_number: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    provider: BaseSMSProvider
) -> Dict[str, Any]:
    """Send appointment reminder SMS"""
    message = f"""
سلام {patient_name} عزیز
یادآوری نوبت شما:
پزشک: دکتر {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}
    """.strip()
    
    return await provider.send_sms(phone_number, message)


async def send_appointment_confirmation(
    phone_number: str,
    appointment_number: str,
    provider: BaseSMSProvider
) -> Dict[str, Any]:
    """Send appointment confirmation SMS"""
    message = f"""
نوبت شما با موفقیت ثبت شد.
شماره نوبت: {appointment_number}
برای مشاهده جزئیات به پنل کاربری خود مراجعه کنید.
    """.strip()
    
    return await provider.send_sms(phone_number, message)
