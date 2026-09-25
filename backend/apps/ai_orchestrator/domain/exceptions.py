"""
Custom exceptions for AI Orchestrator domain.

These exceptions represent domain-specific error conditions.
"""


class AIOrchestratorException(Exception):
    """Base exception for AI Orchestrator"""
    pass


class AIProviderException(AIOrchestratorException):
    """Raised when an AI provider encounters an error"""
    pass


class AIProviderUnavailableException(AIProviderException):
    """Raised when an AI provider is unavailable"""
    pass


class AIProviderTimeoutException(AIProviderException):
    """Raised when an AI provider request times out"""
    pass


class InvalidRequestException(AIOrchestratorException):
    """Raised when request validation fails"""
    pass


class ModelNotFoundException(AIProviderException):
    """Raised when requested model is not found"""
    pass


class QuotaExceededException(AIProviderException):
    """Raised when API quota is exceeded"""
    pass
