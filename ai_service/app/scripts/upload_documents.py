#!/usr/bin/env python3
"""
اسکریپت آپلود دسته‌ای اسناد به سیستم RAG
استفاده: python upload_documents.py <پوشه_اسناد> [--type medical_literature]
"""
import os
import sys
import asyncio
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiohttp
import logging

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# پیکربندی
AI_SERVICE_URL = ("AI_SERVICE_URL", "http://maggicaihub.com:8001")
API_V1_RAG = f"{AI_SERVICE_URL}/api/v1/rag"

# انواع اسناد
SOURCE_TYPES = {
    "1": {"key": "medical_literature", "label": "مستندات پزشکی", "dir": "medical"},
    "2": {"key": "clinical_guidelines", "label": "راهنماهای بالینی", "dir": "guidelines"},
    "3": {"key": "drug_database", "label": "اطلاعات دارویی", "dir": "drugs"},
    "4": {"key": "faq_knowledge", "label": "سوالات متداول", "dir": "faq"},
    "5": {"key": "hospital_policies", "label": "سیاست‌های بیمارستان", "dir": "policies"},
}


class DocumentUploader:
    """کلاس آپلود اسناد به سیستم RAG"""
    
    def __init__(self, base_url: str = AI_SERVICE_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_health(self) -> bool:
        """بررسی سلامت سرویس AI"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"❌ سرویس AI در دسترس نیست: {e}")
            return False
    
    async def upload_document(
        self,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """آپلود یک سند"""
        
        if not os.path.exists(file_path):
            return {
                "file": os.path.basename(file_path),
                "status": "error",
                "error": "فایل یافت نشد"
            }
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(file_path)
            
            # ایجاد FormData
            form = aiohttp.FormData()
            form.add_field(
                'file',
                file_content,
                filename=filename,
                content_type=self._get_content_type(filename)
            )
            
            # اضافه کردن متادیتا
            for key, value in metadata.items():
                form.add_field(key, str(value))
            
            # ارسال درخواست
            async with self.session.post(
                f"{API_V1_RAG}/ingest",
                data=form,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    return {
                        "file": filename,
                        "status": "success",
                        "chunks": result.get("chunks_processed", 0),
                        "message": result.get("message", "OK")
                    }
                else:
                    return {
                        "file": filename,
                        "status": "error",
                        "error": result.get("detail", "Unknown error")
                    }
                    
        except asyncio.TimeoutError:
            return {
                "file": os.path.basename(file_path),
                "status": "error",
                "error": "Timeout - فایل بسیار بزرگ است"
            }
        except Exception as e:
            logger.error(f"خطا در آپلود {file_path}: {e}")
            return {
                "file": os.path.basename(file_path),
                "status": "error",
                "error": str(e)
            }
    
    def _get_content_type(self, filename: str) -> str:
        """تعیین نوع محتوا بر اساس پسوند فایل"""
        ext = Path(filename).suffix.lower()
        types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.html': 'text/html',
        }
        return types.get(ext, 'application/octet-stream')
    
    async def upload_batch(
        self,
        directory: str,
        source_type: str,
        language: str = "fa",
        title_prefix: str = ""
    ) -> Dict[str, Any]:
        """آپلود دسته‌ای اسناد"""
        
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.error(f"❌ پوشه یافت نشد: {directory}")
            return {"success": 0, "error": 0, "files": []}
        
        # یافتن تمام فایل‌های قابل پشتیبانی
        extensions = ['.pdf', '.txt', '.md']
        files = []
        for ext in extensions:
            files.extend(dir_path.glob(f"**/*{ext}"))
        
        if not files:
            logger.warning(f"⚠️ هیچ فایل قابل پردازش یافت نشد")
            return {"success": 0, "error": 0, "files": []}
        
        logger.info(f"📚 {len(files)} فایل یافت شد")
        
        # آپلود تمام فایل‌ها
        results = []
        for i, file_path in enumerate(files, 1):
            logger.info(f"  [{i}/{len(files)}] در حال آپلود: {file_path.name}")
            
            metadata = {
                "title": f"{title_prefix}{file_path.stem}",
                "source_type": source_type,
                "language": language,
                "category": file_path.parent.name if file_path.parent != dir_path else "general"
            }
            
            result = await self.upload_document(str(file_path), metadata)
            results.append(result)
            
            if result["status"] == "success":
                logger.info(f"    ✅ موفق ({result.get('chunks', 0)} chunks)")
            else:
                logger.error(f"    ❌ ناموفق: {result.get('error', 'Unknown')}")
        
        # آمار
        success = sum(1 for r in results if r["status"] == "success")
        errors = sum(1 for r in results if r["status"] == "error")
        
        return {
            "success": success,
            "error": errors,
            "total": len(files),
            "files": results
        }


async def main():
    parser = argparse.ArgumentParser(
        description="آپلود اسناد به سیستم RAG هوش مصنوعی",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
مثال‌ها:
  python upload_documents.py ./medical_docs
  python upload_documents.py ./docs --type medical_literature --lang fa
  python upload_documents.py ./drugs --type drug_database --prefix "دارو: "
        """
    )
    
    parser.add_argument(
        "directory",
        help="پوشه حاوی فایل‌های PDF یا TXT"
    )
    parser.add_argument(
        "--type", "-t",
        choices=[t["key"] for t in SOURCE_TYPES.values()],
        default="medical_literature",
        help="نوع سند (پیش‌فرض: medical_literature)"
    )
    parser.add_argument(
        "--lang", "-l",
        default="fa",
        help="زبان اسناد (پیش‌فرض: fa)"
    )
    parser.add_argument(
        "--prefix", "-p",
        default="",
        help="پیشوند عنوان اسناد"
    )
    parser.add_argument(
        "--url",
        default=AI_SERVICE_URL,
        help="آدرس سرویس AI"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("🚀 آپلود اسناد به سیستم RAG")
    print("="*50)
    print(f"📁 پوشه: {args.directory}")
    print(f"📋 نوع سند: {args.type}")
    print(f"🌐 زبان: {args.lang}")
    print(f"🔗 آدرس سرویس: {args.url}")
    print("="*50 + "\n")
    
    # بررسی وجود پوشه
    if not os.path.isdir(args.directory):
        print(f"❌ خطا: پوشه '{args.directory}' وجود ندارد")
        sys.exit(1)
    
    async with DocumentUploader(args.url) as uploader:
        # بررسی سلامت سرویس
        print("🔍 بررسی سلامت سرویس AI...")
        if not await uploader.check_health():
            print("❌ سرویس AI در دسترس نیست!")
            print("   لطفاً سرویس را اجرا کنید: docker-compose up ai_service")
            sys.exit(1)
        print("✅ سرویس سالم است\n")
        
        # آپلود
        print("📤 شروع آپلود...\n")
        results = await uploader.upload_batch(
            directory=args.directory,
            source_type=args.type,
            language=args.lang,
            title_prefix=args.prefix
        )
        
        # نتایج
        print("\n" + "="*50)
        print("📊 نتایج آپلود")
        print("="*50)
        print(f"✅ موفق: {results['success']}")
        print(f"❌ ناموفق: {results['error']}")
        print(f"📚 کل: {results['total']}")
        print("="*50 + "\n")
        
        if results['error'] > 0:
            print("⚠️ فایل‌های ناموفق:")
            for f in results['files']:
                if f['status'] == 'error':
                    print(f"  - {f['file']}: {f.get('error', 'Unknown')}")
            sys.exit(1)
        
        print("🎉 تمام اسناد با موفقیت آپلود شدند!")
        print("\n💡 اکنون می‌توانید از چت AI استفاده کنید.")


if __name__ == "__main__":
    asyncio.run(main())

