"""Core utilities and helpers"""
import uuid
from typing import Any, Dict
from datetime import datetime, date
import json


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def generate_unique_code(prefix: str = "", length: int = 8) -> str:
    """Generate unique code with optional prefix"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=length))
    return f"{prefix}{code}" if prefix else code


def persian_to_gregorian_date(persian_date: str) -> date:
    """Convert Persian date string to Gregorian date"""
    # Placeholder - implement with jdatetime if needed
    pass


def gregorian_to_persian_date(gregorian_date: date) -> str:
    """Convert Gregorian date to Persian date string"""
    # Placeholder - implement with jdatetime if needed
    pass
