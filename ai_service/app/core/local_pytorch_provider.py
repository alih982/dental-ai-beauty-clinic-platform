# app/core/local_pytorch_provider.py

import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from app.config import settings

logger = logging.getLogger(__name__)

class LocalPyTorchProvider:
    _model = None
    _tokenizer = None

    @classmethod
    def load_model(cls):
        if cls._model is None or cls._tokenizer is None:
            model_path = settings.LOCAL_MODEL_PATH
            logger.info(f"در حال بارگذاری مدل PyTorch از مسیر: {model_path}...")

            # بارگذاری توکنایزر و مدل از مسیر محلی
            # trust_remote_code=True در صورت نیاز به کدهای سفارشی مدل
            cls._tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            
            # بارگذاری مدل با تنظیمات بهینه
            cls._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,  # استفاده از bfloat16 برای بهینه‌سازی حافظه و سرعت
                device_map="auto",            # توزیع خودکار بین CPU/GPU
                trust_remote_code=True
            )
            
            # اگر توکن pad وجود نداشت، از eos_token استفاده کن
            if cls._tokenizer.pad_token is None:
                cls._tokenizer.pad_token = cls._tokenizer.eos_token
                
            logger.info("مدل PyTorch با موفقیت بارگذاری شد.")
        return cls._model, cls._tokenizer

    @classmethod
    async def generate(cls, prompt: str, system_prompt: str = None, max_new_tokens: int = 512):
        """تولید پاسخ بر اساس پرامپت ورودی"""
        model, tokenizer = cls.load_model()
        
        # ساخت پرامپت نهایی با رعایت ساختار Gemma
        if system_prompt:
            full_prompt = f"<bos><start_of_turn>system\n{system_prompt}<end_of_turn>\n<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        else:
            full_prompt = f"<bos><start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        
        # توکنایز کردن ورودی
        inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
        
        # تولید خروجی
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # دی‌توکنایز کردن و استخراج پاسخ
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # حذف بخش پرامپت از پاسخ نهایی
        response = generated_text.split("<start_of_turn>model\n")[-1].strip()
        
        return response

    @classmethod
    async def health_check(cls):
        try:
            await cls.generate("Hi", max_new_tokens=5)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False