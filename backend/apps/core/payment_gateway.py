"""
Payment Gateway Service - Multi-provider support
Supports: Zarinpal (Iran), Stripe (International)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
from enum import Enum
import logging
from datetime import datetime
import httpx

logger = logging.getLogger('apps.payments')


class PaymentProvider(str, Enum):
    """Supported payment providers"""
    ZARINPAL = 'zarinpal'
    STRIPE = 'stripe'


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    CANCELLED = 'cancelled'


class BasePaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    async def create_payment(
        self, 
        amount: Decimal, 
        description: str,
        callback_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a payment request"""
        pass
    
    @abstractmethod
    async def verify_payment(
        self, 
        authority: str,
        amount: Decimal,
        **kwargs
    ) -> Dict[str, Any]:
        """Verify a payment"""
        pass
    
    @abstractmethod
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Refund a payment"""
        pass


class ZarinpalGateway(BasePaymentGateway):
    """
    Zarinpal payment gateway integration (Iranian payment gateway).
    Docs: http://docs.zarinpal.com/paymentGateway/
    """
    
    SANDBOX_URL = 'http://sandbox.zarinpal.com/pg/rest/WebGate/'
    PRODUCTION_URL = 'http://api.zarinpal.com/pg/v4/payment/'
    
    def __init__(self, merchant_id: str, sandbox: bool = False):
        self.merchant_id = merchant_id
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def create_payment(
        self,
        amount: Decimal,
        description: str,
        callback_url: str,
        mobile: str = None,
        email: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create payment request with Zarinpal.
        
        Returns:
            {
                'success': bool,
                'authority': str,  # Payment authority code
                'payment_url': str  # URL to redirect user
            }
        """
        try:
            # Amount must be in Rials
            amount_rials = int(amount)
            
            payload = {
                'merchant_id': self.merchant_id,
                'amount': amount_rials,
                'description': description,
                'callback_url': callback_url,
            }
            
            if mobile:
                payload['mobile'] = mobile
            if email:
                payload['email'] = email
            
            response = await self.client.post(
                f'{self.base_url}request.json',
                json=payload
            )
            
            data = response.json()
            
            if data.get('data', {}).get('code') == 100:
                authority = data['data']['authority']
                payment_url = f'http://www.zarinpal.com/pg/StartPay/{authority}'
                
                logger.info(f"Zarinpal payment created: {authority}")
                
                return {
                    'success': True,
                    'authority': authority,
                    'payment_url': payment_url
                }
            else:
                logger.error(f"Zarinpal error: {data}")
                return {
                    'success': False,
                    'error': data.get('errors', {}).get('message', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Zarinpal create payment error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def verify_payment(
        self,
        authority: str,
        amount: Decimal,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Verify Zarinpal payment.
        
        Returns:
            {
                'success': bool,
                'ref_id': str,  # Reference ID for successful payment
                'card_pan': str  # Masked card number
            }
        """
        try:
            amount_rials = int(amount)
            
            payload = {
                'merchant_id': self.merchant_id,
                'amount': amount_rials,
                'authority': authority
            }
            
            response = await self.client.post(
                f'{self.base_url}verify.json',
                json=payload
            )
            
            data = response.json()
            
            if data.get('data', {}).get('code') == 100:
                logger.info(f"Zarinpal payment verified: {authority}")
                return {
                    'success': True,
                    'ref_id': data['data']['ref_id'],
                    'card_pan': data['data'].get('card_pan', ''),
                }
            else:
                return {
                    'success': False,
                    'error': data.get('errors', {}).get('message', 'Verification failed')
                }
        
        except Exception as e:
            logger.error(f"Zarinpal verify error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Zarinpal refund implementation"""
        # Zarinpal refunds must be done through their panel
        return {
            'success': False,
            'error': 'Refunds must be processed through Zarinpal merchant panel'
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class StripeGateway(BasePaymentGateway):
    """
    Stripe payment gateway integration (International).
    Requires: pip install stripe
    """
    
    def __init__(self, secret_key: str):
        import stripe
        self.stripe = stripe
        self.stripe.api_key = secret_key
    
    async def create_payment(
        self,
        amount: Decimal,
        description: str,
        callback_url: str,
        currency: str = 'usd',
        **kwargs
    ) -> Dict[str, Any]:
        """Create Stripe payment intent"""
        try:
            # Stripe uses smallest currency unit (cents for USD)
            amount_cents = int(amount * 100)
            
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                description=description,
                metadata=kwargs.get('metadata', {}),
            )
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
            }
        
        except Exception as e:
            logger.error(f"Stripe create payment error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def verify_payment(
        self,
        authority: str,
        amount: Decimal,
        **kwargs
    ) -> Dict[str, Any]:
        """Verify Stripe payment"""
        try:
            intent = self.stripe.PaymentIntent.retrieve(authority)
            
            if intent.status == 'succeeded':
                return {
                    'success': True,
                    'payment_method': intent.payment_method,
                }
            else:
                return {
                    'success': False,
                    'error': f'Payment status: {intent.status}'
                }
        
        except Exception as e:
            logger.error(f"Stripe verify error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Refund Stripe payment"""
        try:
            refund_data = {'payment_intent': transaction_id}
            
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            refund = self.stripe.Refund.create(**refund_data)
            
            return {
                'success': True,
                'refund_id': refund.id,
                'status': refund.status
            }
        
        except Exception as e:
            logger.error(f"Stripe refund error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


class PaymentGatewayFactory:
    """Factory for creating payment gateway instances"""
    
    @staticmethod
    def create_gateway(
        provider: PaymentProvider,
        **config
    ) -> BasePaymentGateway:
        """Create payment gateway instance"""
        
        if provider == PaymentProvider.ZARINPAL:
            return ZarinpalGateway(
                merchant_id=config.get('merchant_id'),
                sandbox=config.get('sandbox', False)
            )
        
        elif provider == PaymentProvider.STRIPE:
            return StripeGateway(
                secret_key=config.get('secret_key')
            )
        
        else:
            raise ValueError(f"Unsupported payment provider: {provider}")
