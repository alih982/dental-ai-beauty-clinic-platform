"""
Base Validators Module - Common validation logic

Provides:
- Reusable validators
- Validation helpers
- Error formatting
"""
from django.core.exceptions import ValidationError
from typing import Any, Dict, List
from django.utils.deconstruct import deconstructible
import re


@deconstructible
class BaseValidator:
    """Base validator class"""
    
    def __init__(self, message: str = "Validation failed"):
        self.message = message
    
    def __call__(self, value: Any):
        """Override in subclass"""
        raise NotImplementedError


class PhoneNumberValidator(BaseValidator):
    """Validate Iranian phone numbers"""
    
    def __init__(self, message: str = "شماره تلفن معتبر نیست"):
        super().__init__(message)
        self.pattern = re.compile(r'^09[0-9]{9}$')
    
    def __call__(self, value: str):
        if not self.pattern.match(value):
            raise ValidationError(self.message)
        return value


class NationalCodeValidator(BaseValidator):
    """Validate Iranian national code"""
    
    def __init__(self, message: str = "کد ملی معتبر نیست"):
        super().__init__(message)
    
    def __call__(self, value: str):
        if not value or len(value) != 10:
            raise ValidationError(self.message)
        
        if not value.isdigit():
            raise ValidationError(self.message)
        
        # Check sum algorithm for Iranian national code
        check_digit = int(value[9])
        sum_digits = sum(int(value[i]) * (10 - i) for i in range(9))
        remainder = sum_digits % 11
        
        valid = (remainder < 2 and check_digit == remainder) or \
                (remainder >= 2 and check_digit == 11 - remainder)
        
        if not valid:
            raise ValidationError(self.message)
        
        return value


class RequiredFieldsValidator:
    """Validate required fields in dictionary"""
    
    def __init__(self, required_fields: List[str]):
        self.required_fields = required_fields
    
    def __call__(self, data: Dict[str, Any]):
        missing_fields = []
        for field in self.required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                f"فیلدهای الزامی وجود ندارند: {', '.join(missing_fields)}"
            )
        
        return data


class DateRangeValidator(BaseValidator):
    """Validate date is within range"""
    
    def __init__(self, start_date=None, end_date=None, 
                 message: str = "تاریخ خارج از محدوده مجاز است"):
        super().__init__(message)
        self.start_date = start_date
        self.end_date = end_date
    
    def __call__(self, value):
        from datetime import date
        
        if self.start_date and value < self.start_date:
            raise ValidationError(self.message)
        
        if self.end_date and value > self.end_date:
            raise ValidationError(self.message)
        
        return value


def validate_email(email: str) -> str:
    """Validate email format"""
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        raise ValidationError("فرمت ایمیل صحیح نیست")
    return email


def validate_positive_number(value: float) -> float:
    """Validate number is positive"""
    if value <= 0:
        raise ValidationError("مقدار باید بزرگتر از صفر باشد")
    return value
