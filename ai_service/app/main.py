# """
# FastAPI AI Service - Main Application (Fixed for Standalone)
# Integration with Ollama llama3.2 for medical assistance
# """
# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import logging

# from app.api.v1 import chat, health, rag, websocket, control
# from app.config import settings
# from app.infrastructure.vector_store import init_db

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Create FastAPI app
# app = FastAPI(
#     title="Smart Health AI Service",
#     description="AI-powered medical assistant using llama3.2",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc"
# )

# # CORS middleware - fixed for compatibility
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(health.router, prefix="/api/v1", tags=["Health"])
# app.include_router(chat.router, prefix="/api/v1", tags=["AI Chat"])
# app.include_router(rag.router, prefix="/api/v1", tags=["RAG System"])
# app.include_router(control.router, prefix="/api/v1", tags=["AI Control"])
# app.include_router(websocket.router, tags=["WebSocket"])


# @app.on_event("startup")
# async def startup_event():
#     """Initialize services on startup"""
#     logger.info("Starting AI Service...")
    
#     # Initialize Database for RAG
#     # try:
#     #     init_db()
#     #     logger.info("Database initialized for RAG.")
#     # except Exception as e:
#     #     logger.error(f"Failed to initialize database: {e}")

#     # logger.info(f"Provider: {settings.AI_PROVIDER}")
#     # logger.info(f"Ollama host: {settings.OLLAMA_HOST}")
#     # logger.info(f"Model: {settings.OLLAMA_MODEL}")
    
#     # # Check provider health
#     from app.core.provider import AIProviderFactory
#     provider = AIProviderFactory.get_provider()
#     is_healthy = await provider.health_check()
#     if is_healthy:
#         logger.info("AI Provider is healthy.")
#     else:
#         logger.warning("AI Provider health check failed on startup.")


# @app.on_event("shutdown")
# async def shutdown_event():
#     """Cleanup on shutdown"""
#     logger.info("Shutting down AI Service...")


# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {
#         "service": "Smart Health AI Service",
#         "version": "1.0.0",
#         "status": "running",
#         "docs": "/docs"
#     }


# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     """Global exception handler"""
#     logger.error(f"Unhandled exception: {exc}", exc_info=True)
#     return JSONResponse(
#         status_code=500,
#         content={
#             "success": False,
#             "message": "خطای سیستمی رخ داده است",
#             "detail": str(exc) if settings.DEBUG else None
#         }
#     )

# if __name__ == "__main__":
#     """Standalone server run - no Docker needed!"""
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=5000,
#         reload=settings.DEBUG,
#         log_level="info"
#     )
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
MODEL_PATH = "app/lora_model"
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://maggicaihub.com",
    "http://www.maggicaihub.com",
    "http://magicai.runflare.run",
]
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ALPACA_PROMPT = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

model = None
tokenizer = None
_load_error: str | None = None

def load_model():
    global model, tokenizer
    if model is not None:
        return
    logger.info(f"Loading model from {MODEL_PATH} ...")
    
    # Check required libraries
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import sentencepiece
        import google.protobuf
    except ImportError as e:
        logger.error(f"Missing required library: {e}")
        logger.error("Please install: pip install protobuf sentencepiece transformers torch")
        raise
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    if device == "cpu":
        model = model.to(device)
    model.eval()
    logger.info("Model loaded successfully.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Service...")
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, load_model)
        logger.info("Model is ready.")
    except Exception as e:
        logger.error(f"Model loading failed: {e}", exc_info=True)
        logger.error("Please ensure protobuf and sentencepiece are installed: pip install protobuf sentencepiece")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Smart Health AI Service",
    description="Local Gemma‑2 fine‑tuned",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    success: bool
    message: str

    # Debug fields (for dev/testing)
    model_loaded: bool = False
    load_error: str | None = None
    error_stage: str | None = None

# track loading errors so we can return them to frontend
_load_error: str | None = None

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    global _load_error

    if model is None or tokenizer is None:
        return ChatResponse(
            success=False,
            message="Model not loaded.",
            model_loaded=False,
            load_error=_load_error,
            error_stage="model_not_loaded",
        )

    try:
        prompt = ALPACA_PROMPT.format(request.message, "", "")

        try:
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        except Exception as e:
            raise RuntimeError(f"tokenize_failed: {e}") from e

        try:
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        except Exception as e:
            raise RuntimeError(f"generate_failed: {e}") from e

        try:
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            raise RuntimeError(f"decode_failed: {e}") from e

        if "### Response:" in response:
            response = response.split("### Response:")[-1].strip()

        return ChatResponse(
            success=True,
            message=response,
            model_loaded=True,
            load_error=None,
            error_stage=None,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        msg = str(e)

        # crude stage extraction
        stage = None
        for s in ["tokenize_failed", "generate_failed", "decode_failed"]:
            if msg.startswith(s):
                stage = s
                break

        return ChatResponse(
            success=False,
            message=f"Error: {msg}",
            model_loaded=model is not None,
            load_error=_load_error,
            error_stage=stage or "unknown",
        )

@app.get("/")
async def root():
    return {"service": "Local Gemma‑2", "status": "running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False, log_level="info")