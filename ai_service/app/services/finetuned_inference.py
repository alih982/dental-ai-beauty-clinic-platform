# """
# Fine-tuned model inference service using transformers with PEFT/LoRA support.
# Uses ONLY local files from app/ai_model/ (or configured ADAPTER_PATH).
# Reads base model name dynamically from adapter_config.json.
# """
# import os
# import logging
# from typing import AsyncGenerator, Optional
# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM
# from peft import PeftModel
# import json

# from app.config import settings

# logger = logging.getLogger(__name__)

# class FineTunedModelService:
#     """
#     Service for running inference with fine-tuned models (LoRA adapters).
#     Loads tokenizer from LOCAL adapter folder.
#     Reads base model from adapter_config.json (NOT hardcoded).
#     """
#     _instance = None
#     _model = None
#     _tokenizer = None
#     _is_loaded = False
    
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#         return cls._instance
    
#     async def load_model(self):
#         """Load the fine-tuned model and tokenizer from local files."""
#         if self._is_loaded:
#             logger.info("Model already loaded")
#             return
        
#         try:
#             adapter_path = settings.ADAPTER_PATH  # e.g., app/ai_model
            
#             # 1) Read base model name from LOCAL adapter_config.json
#             adapter_config_path = os.path.join(adapter_path, "adapter_config.json")
#             if os.path.exists(adapter_config_path):
#                 with open(adapter_config_path, 'r', encoding='utf-8') as f:
#                     adapter_config = json.load(f)
#                 base_model_path = adapter_config.get("base_model_name_or_path")
#                 logger.info(f"Base model from adapter config: {base_model_path}")
#             else:
#                 # Should never happen if model folder is correct
#                 base_model_path = "unsloth/gemma-2-2b-bnb-4bit"
#                 logger.warning(f"No adapter_config.json found, using fallback: {base_model_path}")
            
#             # 2) Load tokenizer from LOCAL adapter folder (fine-tuned tokenizer files)
#             logger.info(f"Loading tokenizer from local path: {adapter_path}")
#             self._tokenizer = AutoTokenizer.from_pretrained(
#                 adapter_path,
#                 trust_remote_code=True
#             )
#             if self._tokenizer.pad_token is None:
#                 self._tokenizer.pad_token = self._tokenizer.eos_token
            
#             # 3) Load base model (from HuggingFace cache or download)
#             #    This is the model the LoRA was trained on (read from adapter_config.json)
#             logger.info(f"Loading base model weights: {base_model_path}")
            
#             # Detect if base model is quantized (bnb/4bit/8bit)
#             is_quantized = any(q in base_model_path.lower() for q in ["bnb", "4bit", "8bit", "gptq", "awq"])
            
#             if is_quantized:
#                 # Try quantized loading first (for GPU or CPU with bitsandbytes)
#                 try:
#                     from transformers import BitsAndBytesConfig
#                     quant_config = BitsAndBytesConfig(
#                         load_in_4bit=True,
#                         bnb_4bit_compute_dtype=torch.float16,
#                         bnb_4bit_use_double_quant=True,
#                         bnb_4bit_quant_type="nf4"
#                     )
#                     self._model = AutoModelForCausalLM.from_pretrained(
#                         base_model_path,
#                         quantization_config=quant_config,
#                         device_map="auto",
#                         trust_remote_code=True,
#                         low_cpu_mem_usage=True
#                     )
#                     logger.info("Base model loaded with 4-bit quantization")
#                 except Exception as e:
#                     logger.warning(f"Quantized loading failed: {e}. Trying CPU float32 fallback.")
#                     self._model = AutoModelForCausalLM.from_pretrained(
#                         base_model_path,
#                         torch_dtype=torch.float32,
#                         device_map="cpu",
#                         low_cpu_mem_usage=True,
#                         trust_remote_code=True
#                     )
#                     logger.info("Base model loaded on CPU (float32)")
#             else:
#                 # Non-quantized base model
#                 self._model = AutoModelForCausalLM.from_pretrained(
#                     base_model_path,
#                     torch_dtype=torch.float32,
#                     device_map="cpu",
#                     low_cpu_mem_usage=True,
#                     trust_remote_code=True
#                 )
#                 logger.info("Base model loaded on CPU (float32)")
            
#             # 4) Apply LoRA adapters from LOCAL folder
#             logger.info(f"Loading LoRA adapters from: {adapter_path}")
#             self._model = PeftModel.from_pretrained(
#                 self._model,
#                 adapter_path,
#                 is_trainable=False
#             )
#             logger.info("LoRA adapters merged successfully")
            
#             # Set to evaluation mode
#             self._model.eval()
            
#             self._is_loaded = True
#             logger.info("Fine-tuned model loaded and ready for inference!")
            
#         except Exception as e:
#             logger.error(f"Failed to load model: {e}", exc_info=True)
#             raise
    
#     async def generate(
#         self,
#         message: str,
#         history: list = None,
#         system_prompt: Optional[str] = None,
#         temperature: float = 0.7,
#         max_tokens: int = 2048,
#         model_name: str = None  # ignored, always uses loaded model
#     ) -> AsyncGenerator[str, None]:
#         """
#         Generate streaming response from the fine-tuned model.
#         """
#         if not self._is_loaded:
#             await self.load_model()
        
#         # Build conversation prompt
#         prompt = self._build_prompt(message, history or [], system_prompt)
        
#         # Tokenize input
#         inputs = self._tokenizer(
#             prompt,
#             return_tensors="pt",
#             padding=True,
#             truncation=True,
#             max_length=settings.MAX_SEQ_LENGTH
#         ).to(self._model.device)
        
#         # Generate with streaming
#         from transformers import TextIteratorStreamer
#         from threading import Thread
        
#         streamer = TextIteratorStreamer(
#             self._tokenizer,
#             skip_prompt=True,
#             skip_special_tokens=True
#         )
        
#         generation_kwargs = {
#             **inputs,
#             "max_new_tokens": max_tokens,
#             "temperature": temperature,
#             "top_p": settings.TOP_P,
#             "do_sample": temperature > 0,
#             "streamer": streamer,
#         }
        
#         thread = Thread(target=self._model.generate, kwargs=generation_kwargs)
#         thread.start()
        
#         # Yield generated tokens
#         for text in streamer:
#             yield text
        
#         thread.join()
    
#     def _build_prompt(
#         self,
#         message: str,
#         history: list,
#         system_prompt: Optional[str] = None
#     ) -> str:
#         """Build Gemma chat prompt from message history."""
        
#         if system_prompt is None:
#             system_prompt = """You are DoctorHub AI, a knowledgeable medical assistant. 
# Answer in Persian/Farsi. Provide helpful, accurate medical information. 
# Always recommend consulting a healthcare professional for diagnosis or treatment."""
        
#         conversation = f"<start_of_turn>system\n{system_prompt}<end_of_turn>\n"
        
#         for msg in history:
#             role = msg.get("role", "user")
#             content = msg.get("content", "")
#             if role == "user":
#                 conversation += f"<start_of_turn>user\n{content}<end_of_turn>\n"
#             else:
#                 conversation += f"<start_of_turn>model\n{content}<end_of_turn>\n"
        
#         conversation += f"<start_of_turn>user\n{message}<end_of_turn>\n"
#         conversation += "<start_of_turn>model\n"
        
#         return conversation
    
#     async def health_check(self) -> bool:
#         """Check if model is loaded and ready."""
#         return self._is_loaded
    
#     def unload_model(self):
#         """Unload model from memory."""
#         if self._model is not None:
#             del self._model
#             self._model = None
#         if self._tokenizer is not None:
#             del self._tokenizer
#             self._tokenizer = None
#         self._is_loaded = False
        
#         if torch.cuda.is_available():
#             torch.cuda.empty_cache()
        
#         logger.info("Model unloaded from memory")


# # Singleton instance
# fine_tuned_service = FineTunedModelService()

"""
Fine-tuned model inference service using transformers.
Loads model directly from LOCAL folder (app/ai_model/).
Supports Gemma 2 fine-tuned models in .safetensors or .pt format.
"""
import logging
from typing import AsyncGenerator, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from threading import Thread
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)

class FineTunedModelService:
    _instance = None
    _model = None
    _tokenizer = None
    _is_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def load_model(self):
        """Load the full fine-tuned model and tokenizer from local folder."""
        if self._is_loaded:
            logger.info("Model already loaded")
            return

        model_path = settings.AI_MODEL_PATH  # "app/ai_model"
        logger.info(f"Loading fine-tuned model from {model_path} ...")

        try:
            # 1) Load tokenizer from local folder
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            # 2) Load model (full fine-tuned weights)
            # Determine device and dtype
            if torch.cuda.is_available() and not settings.USE_QUANTIZATION:
                torch_dtype = torch.bfloat16
                device_map = "auto"
                logger.info("Loading model on GPU with bfloat16")
            elif settings.USE_QUANTIZATION:
                # Optional 4-bit quantization if enabled in config
                try:
                    from transformers import BitsAndBytesConfig
                    quant_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    self._model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        quantization_config=quant_config,
                        device_map="auto",
                        trust_remote_code=True
                    )
                    logger.info("Model loaded with 4-bit quantization")
                except Exception as e:
                    logger.warning(f"Quantization failed: {e}. Falling back to CPU.")
                    torch_dtype = torch.float32
                    device_map = "cpu"
                    self._model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        torch_dtype=torch_dtype,
                        device_map=device_map,
                        trust_remote_code=True
                    )
            else:
                # CPU or GPU without quantization
                torch_dtype = torch.float32
                device_map = "cpu" if not torch.cuda.is_available() else "auto"
                self._model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch_dtype,
                    device_map=device_map,
                    trust_remote_code=True
                )
                logger.info(f"Model loaded on {device_map} with {torch_dtype}")

            self._model.eval()
            self._is_loaded = True
            logger.info("Fine-tuned model loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise

    async def generate(
        self,
        message: str,
        history: list = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_name: str = None  # ignored
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from the fine-tuned model."""
        if not self._is_loaded:
            await self.load_model()

        # Build conversation prompt (Gemma format)
        prompt = self._build_prompt(message, history or [], system_prompt)

        # Tokenize
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=settings.MAX_SEQ_LENGTH
        )
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Streamer
        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": settings.TOP_P,
            "do_sample": temperature > 0,
            "streamer": streamer,
        }

        thread = Thread(target=self._model.generate, kwargs=generation_kwargs)
        thread.start()

        # Yield tokens as they arrive
        for text in streamer:
            yield text

        thread.join()

    def _build_prompt(
        self,
        message: str,
        history: list,
        system_prompt: Optional[str] = None
    ) -> str:
        """Build Gemma chat prompt."""
        if system_prompt is None:
            system_prompt = (
                "شما یک دستیار پزشکی حاذق هستید که به زبان فارسی پاسخ می‌دهید. "
                "اطلاعات دقیق و مفید ارائه دهید و در صورت نیاز به پزشک مراجعه کنید."
            )

        conversation = f"<start_of_turn>system\n{system_prompt}<end_of_turn>\n"

        for msg in history[-4:]:  # limit history length
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                conversation += f"<start_of_turn>user\n{content}<end_of_turn>\n"
            elif role == "assistant":
                conversation += f"<start_of_turn>model\n{content}<end_of_turn>\n"

        conversation += f"<start_of_turn>user\n{message}<end_of_turn>\n"
        conversation += "<start_of_turn>model\n"
        return conversation

    async def health_check(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded

    def unload_model(self):
        """Free memory."""
        if self._model:
            del self._model
            self._model = None
        if self._tokenizer:
            del self._tokenizer
            self._tokenizer = None
        self._is_loaded = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Model unloaded")

# Singleton instance
fine_tuned_service = FineTunedModelService()