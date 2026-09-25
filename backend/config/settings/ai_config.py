"""
AI Configuration Settings

Centralized configuration for AI providers and orchestration.
"""
import os

# ============================================================================
# AI PROVIDER SETTINGS
# ============================================================================

# Provider type: 'gemma', 'local', 'openai', 'claude'
AI_PROVIDER_TYPE = os.getenv('AI_PROVIDER_TYPE', 'local')

# Model name for the selected provider
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'gemma2:latest')

# API keys (when needed)
AI_API_KEY = os.getenv('AI_API_KEY', None)  # For OpenAI, Claude, etc.

# Base URL for local/self-hosted models
AI_BASE_URL = os.getenv('AI_BASE_URL', 'http://maggicaihub.com:11434')

# Request timeout in seconds
AI_TIMEOUT = int(os.getenv('AI_TIMEOUT', 30))

# Maximum retry attempts
AI_MAX_RETRIES = int(os.getenv('AI_MAX_RETRIES', 3))

# Default generation parameters
AI_DEFAULT_TEMPERATURE = float(os.getenv('AI_DEFAULT_TEMPERATURE', 0.7))
AI_DEFAULT_MAX_TOKENS = int(os.getenv('AI_DEFAULT_MAX_TOKENS', 2000))

# System prompts
AI_MEDICAL_SYSTEM_PROMPT = """You are an AI medical assistant for a healthcare platform.
Provide helpful, accurate medical information while emphasizing that you are not a replacement for professional medical advice.
Always encourage users to consult with qualified healthcare professionals for diagnosis and treatment."""

AI_PRESCRIPTION_SYSTEM_PROMPT = """You are assisting doctors in generating electronic prescriptions.
Suggest medications based on symptoms and diagnosis, including:
- Medication name
- Dosage
- Frequency
- Duration
- Important warnings

Format your response as a structured list."""

# ============================================================================
# WHATSAPP NOTIFICATION SETTINGS
# ============================================================================

# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', None)
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', None)
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', None)
WHATSAPP_API_VERSION = os.getenv('WHATSAPP_API_VERSION', 'v18.0')

# To activate WhatsApp:
# 1. Go to http://developers.facebook.com
# 2. Create Meta Business account
# 3. Set up WhatsApp Business API
# 4. Get access token and phone number ID
# 5. Set environment variables above

# ============================================================================
# SCHEDULING SETTINGS
# ============================================================================

# Reminder times before appointment (in hours)
APPOINTMENT_REMINDER_TIMES = [24, 2]  # 24 hours and 2 hours before

# Working hours
CLINIC_WORKING_HOURS_START = 8  # 8 AM
CLINIC_WORKING_HOURS_END = 17   # 5 PM

# Default appointment duration (minutes)
DEFAULT_APPOINTMENT_DURATION = 30

# ============================================================================
# MLFLOW TRACKING
# ============================================================================

MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://maggicaihub.com:5000')
MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME', 'ai_healthcare')
