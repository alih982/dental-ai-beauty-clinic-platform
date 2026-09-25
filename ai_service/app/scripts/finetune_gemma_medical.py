#!/usr/bin/env python3
"""
Gemma 2B Medical Fine-tuning Script
=====================================
This script fine-tunes Google's Gemma 2B model on medical/patient data 
using LoRA and quantization techniques for deployment.

Author: Hospital Application AI Team
Version: 1.0.0
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Configuration ==============
class Config:
    """Configuration for Gemma fine-tuning"""
    
    # Model Configuration
    MODEL_NAME = "google/gemma-2b"
    MODEL_PATH = "./models/gemma-2b"
    OUTPUT_DIR = "./output/gemma-medical-finetuned"
    
    # Quantization Settings
    QUANTIZATION_CONFIG = {
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": "float16",
        "bnb_4bit_use_double_quant": True,
        "bnb_4bit_quant_type": "nf4"
    }
    
    # LoRA Configuration
    LORA_CONFIG = {
        "r": 16,  # Rank
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        "bias": "none",
        "task_type": "CAUSAL_LM"
    }
    
    # Training Configuration
    TRAINING_CONFIG = {
        "per_device_train_batch_size": 4,
        "per_device_eval_batch_size": 4,
        "gradient_accumulation_steps": 4,
        "learning_rate": 2e-4,
        "num_train_epochs": 3,
        "warmup_ratio": 0.1,
        "logging_steps": 10,
        "save_steps": 100,
        "eval_steps": 100,
        "max_seq_length": 2048,
        "fp16": True,
        "dataloader_num_workers": 4
    }
    
    # Medical Data Paths
    DATA_DIR = "./data/medical"
    PATIENT_DATA_PATH = f"{DATA_DIR}/patient_records.json"
    DOCTOR_DATA_PATH = f"{DATA_DIR}/doctor_info.json"
    MEDICAL_KB_PATH = f"{DATA_DIR}/medical_knowledge.json"
    SYMPTOMS_PATH = f"{DATA_DIR}/symptoms.json"

# ============== Data Preparation ==============
class MedicalDataProcessor:
    """Process medical data for fine-tuning"""
    
    def __init__(self, config: Config):
        self.config = config
        self.data_dir = Path(config.DATA_DIR)
        
    def load_patient_records(self) -> List[Dict]:
        """Load patient records from database/export"""
        path = self.config.PATIENT_DATA_PATH
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_doctor_info(self) -> List[Dict]:
        """Load doctor information"""
        path = self.config.DOCTOR_DATA_PATH
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_medical_knowledge(self) -> List[Dict]:
        """Load medical knowledge base"""
        path = self.config.MEDICAL_KB_PATH
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_symptoms(self) -> List[Dict]:
        """Load symptoms database"""
        path = self.config.SYMPTOMS_PATH
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def create_instruction_dataset(self) -> List[Dict]:
        """Create instruction-following dataset for fine-tuning"""
        dataset = []
        
        # Load all data sources
        patients = self.load_patient_records()
        doctors = self.load_doctor_info()
        medical_kb = self.load_medical_knowledge()
        symptoms = self.load_symptoms()
        
        # ============== Patient Data Examples ==============
        for patient in patients[:100]:  # Limit to 100 examples
            # Patient information query
            dataset.append({
                "instruction": f"اطلاعات بیمار با شماره پرونده {patient.get('record_number', 'N/A')} را شرح دهید.",
                "input": "",
                "output": self._format_patient_info(patient)
            })
            
            # Medical history query
            dataset.append({
                "instruction": f"تاریخچه پزشکی بیمار {patient.get('first_name', '')} {patient.get('last_name', '')} را توضیح دهید.",
                "input": "",
                "output": self._format_medical_history(patient)
            })
            
            # Symptoms query
            dataset.append({
                "instruction": f"علائم بیمار {patient.get('first_name', '')} چیست؟",
                "input": "",
                "output": self._format_symptoms(patient)
            })
        
        # ============== Doctor Information Examples ==============
        for doctor in doctors[:50]:
            dataset.append({
                "instruction": f"اطلاعات پزشک {doctor.get('first_name', '')} {doctor.get('last_name', '')} را توضیح دهید.",
                "input": "",
                "output": self._format_doctor_info(doctor)
            })
            
            # Specialty query
            dataset.append({
                "instruction": f"تخصص پزشک {doctor.get('specialty', 'پزشک عمومی')} چیست؟",
                "input": "",
                "output": f"تخصص این پزشک {doctor.get('specialty', 'پزشک عمومی')} می‌باشد. "
                        f"سوابق تحصیلی: {doctor.get('education', 'N/A')}. "
                        f"سال تجربه: {doctor.get('years_experience', 'N/A')} سال."
            })
        
        # ============== Medical Knowledge Examples ==============
        for kb_item in medical_kb[:100]:
            # Disease description
            dataset.append({
                "instruction": f"بیماری {kb_item.get('name', '')} را توضیح دهید.",
                "input": "",
                "output": self._format_disease_info(kb_item)
            })
            
            # Treatment
            dataset.append({
                "instruction": f"درمان {kb_item.get('name', '')} چیست؟",
                "input": "",
                "output": f"درمان این بیماری شامل: {kb_item.get('treatment', 'N/A')}. "
                        f"داروهای مورد نیاز: {kb_item.get('medications', 'N/A')}."
            })
        
        # ============== Symptoms Examples ==============
        for symptom in symptoms[:50]:
            dataset.append({
                "instruction": f"علت {symptom.get('name', '')} چیست؟",
                "input": "",
                "output": f"{symptom.get('name', '')} می‌تواند نشانه موارد زیر باشد: "
                        f"{', '.join(symptom.get('possible_causes', []))}. "
                        f"توصیه می‌شود با پزشک مشورت کنید."
            })
        
        # ============== General Medical Q&A ==============
        general_qa = [
            {
                "instruction": "چگونه فشار خون را کنترل کنیم؟",
                "output": "برای کنترل فشار خون: 1- رژیم غذایی سالم کم‌نمک داشته باشید. "
                         "2- ورزش منظم روزانه. 3- کاهش استرس. 4- مصرف داروهای تجویز شده. "
                         "5- کنترل منظم فشار خون."
            },
            {
                "instruction": "علائم دیابت چیست؟",
                "output": "علائم دیابت شامل: تشنگی زیاد، تکرر ادرار، خستگی، تاری دید، "
                         "بهبود زخم دیرهنگام. در صورت مشاهده این علائم به پزشک مراجعه کنید."
            },
            {
                "instruction": "چگونه سیستم ایمنی را تقویت کنیم؟",
                "output": "برای تقویت سیستم ایمنی: 1- تغذیه سالم و متوازن. "
                         "2- خواب کافی 7-8 ساعت. 3- ورزش منظم. 4- کاهش استرس. "
                         "5- مصرف ویتامین‌ها. 6- ترک سیگار و الکل."
            },
            {
                "instruction": "علائم بیماری‌های قلبی چیست؟",
                "output": "علائم بیماری‌های قلبی: درد قفسه سینه، تنگی نفس، خستگی زیاد، "
                         "تپش قلب، سرگیجه. در صورت مشاهده این علائم فوراً به پزشک مراجعه کنید."
            },
            {
                "instruction": "چگونه از بیماری‌های عفونی پیشگیری کنیم؟",
                "output": "پیشگیری از بیماری‌های عفونی: 1- شستن دست‌ها مرتب. "
                         "2- واکسیناسیون به موقع. 3- رعایت فاصله اجتماعی در شیوع بیماری. "
                         "4- استفاده از ماسک در صورت نیاز. 5- تقویت سیستم ایمنی."
            }
        ]
        dataset.extend(general_qa)
        
        return dataset
    
    def _format_patient_info(self, patient: Dict) -> str:
        """Format patient information for training"""
        return (f"شماره پرونده: {patient.get('record_number', 'N/A')}\n"
                f"نام: {patient.get('first_name', '')} {patient.get('last_name', '')}\n"
                f"سن: {patient.get('age', 'N/A')} سال\n"
                f"جنسیت: {patient.get('gender', 'N/A')}\n"
                f"گروه خونی: {patient.get('blood_type', 'N/A')}\n"
                f"آلرژی: {patient.get('allergies', 'ندارد')}\n"
                f"بیماری‌های زمینه‌ای: {patient.get('chronic_diseases', 'ندارد')}")
    
    def _format_medical_history(self, patient: Dict) -> str:
        """Format medical history"""
        history = patient.get('medical_history', [])
        if isinstance(history, list):
            history_text = '\n'.join([f"- {h}" for h in history])
        else:
            history_text = str(history)
        
        return (f"سوابق پزشکی بیمار:\n{history_text}\n\n"
                f"جراحی‌ها: {patient.get('surgeries', 'ندارد')}\n"
                f"داروهای فعلی: {patient.get('current_medications', 'ندارد')}")
    
    def _format_symptoms(self, patient: Dict) -> str:
        """Format patient symptoms"""
        symptoms = patient.get('current_symptoms', [])
        if isinstance(symptoms, list):
            symptoms_text = '\n'.join([f"- {s}" for s in symptoms])
        else:
            symptoms_text = str(symptoms)
        
        return f"علائم فعلی بیمار:\n{symptoms_text}"
    
    def _format_doctor_info(self, doctor: Dict) -> str:
        """Format doctor information"""
        return (f"پزشک: دکتر {doctor.get('first_name', '')} {doctor.get('last_name', '')}\n"
                f"تخصص: {doctor.get('specialty', 'N/A')}\n"
                f"تحصیلات: {doctor.get('education', 'N/A')}\n"
                f"سوابق کاری: {doctor.get('years_experience', 'N/A')} سال\n"
                f"شماره نظام پزشکی: {doctor.get('medical_license', 'N/A')}")
    
    def _format_disease_info(self, kb_item: Dict) -> str:
        """Format disease information"""
        return (f"بیماری: {kb_item.get('name', 'N/A')}\n"
                f"توضیحات: {kb_item.get('description', 'N/A')}\n"
                f"علائم: {kb_item.get('symptoms', 'N/A')}\n"
                f"درمان: {kb_item.get('treatment', 'N/A')}\n"
                f"پیشگیری: {kb_item.get('prevention', 'N/A')}")

    def save_dataset(self, dataset: List[Dict], output_path: str):
        """Save dataset to JSON file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        logger.info(f"Dataset saved to {output_path} with {len(dataset)} examples")


# ============== Model Training ==============
class GemmaFineTuner:
    """Fine-tune Gemma model on medical data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
    def setup_model(self):
        """Load and configure Gemma model with quantization"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            from peft import LoraConfig, get_peft_model, TaskType
            
            logger.info("Loading Gemma model with 4-bit quantization...")
            
            # Configure quantization
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=self.config.QUANTIZATION_CONFIG["load_in_4bit"],
                bnb_4bit_compute_dtype=getattr(
                    __import__('torch'), 
                    self.config.QUANTIZATION_CONFIG["bnb_4bit_compute_dtype"]
                ),
                bnb_4bit_use_double_quant=self.config.QUANTIZATION_CONFIG["bnb_4bit_use_double_quant"],
                bnb_4bit_quant_type=self.config.QUANTIZATION_CONFIG["bnb_4bit_quant_type"]
            )
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.MODEL_NAME,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True
            )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.MODEL_NAME,
                trust_remote_code=True
            )
            
            # Configure LoRA
            lora_config = LoraConfig(
                r=self.config.LORA_CONFIG["r"],
                lora_alpha=self.config.LORA_CONFIG["lora_alpha"],
                lora_dropout=self.config.LORA_CONFIG["lora_dropout"],
                target_modules=self.config.LORA_CONFIG["target_modules"],
                bias=self.config.LORA_CONFIG["bias"],
                task_type=TaskType.CAUSAL_LM
            )
            
            # Apply LoRA
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()
            
            logger.info("Model loaded successfully!")
            return True
            
        except ImportError as e:
            logger.error(f"Required packages not installed: {e}")
            logger.info("Installing required packages...")
            return False
    
    def prepare_dataset(self, dataset_path: str):
        """Prepare dataset for training"""
        from transformers import Dataset
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Format for training
        def format_example(example):
            return f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"
        
        formatted_data = [format_example(d) for d in data]
        
        # Create dataset (simplified)
        dataset = Dataset.from_dict({"text": formatted_data})
        
        # Tokenize
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=self.config.TRAINING_CONFIG["max_seq_length"]
            )
        
        return dataset.map(tokenize_function, batched=True)
    
    def train(self, dataset):
        """Train the model"""
        from transformers import TrainingArguments, Trainer
        
        training_args = TrainingArguments(
            output_dir=self.config.OUTPUT_DIR,
            num_train_epochs=self.config.TRAINING_CONFIG["num_train_epochs"],
            per_device_train_batch_size=self.config.TRAINING_CONFIG["per_device_train_batch_size"],
            per_device_eval_batch_size=self.config.TRAINING_CONFIG["per_device_eval_batch_size"],
            gradient_accumulation_steps=self.config.TRAINING_CONFIG["gradient_accumulation_steps"],
            learning_rate=self.config.TRAINING_CONFIG["learning_rate"],
            warmup_ratio=self.config.TRAINING_CONFIG["warmup_ratio"],
            logging_steps=self.config.TRAINING_CONFIG["logging_steps"],
            save_steps=self.config.TRAINING_CONFIG["save_steps"],
            fp16=self.config.TRAINING_CONFIG["fp16"],
            dataloader_num_workers=self.config.TRAINING_CONFIG["dataloader_num_workers"],
            report_to="none"
        )
        
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset
        )
        
        logger.info("Starting training...")
        self.trainer.train()
        logger.info("Training completed!")
    
    def save_model(self):
        """Save fine-tuned model"""
        self.model.save_pretrained(self.config.OUTPUT_DIR)
        self.tokenizer.save_pretrained(self.config.OUTPUT_DIR)
        logger.info(f"Model saved to {self.config.OUTPUT_DIR}")
    
    def convert_to_gguf(self):
        """Convert model to GGUF format for Ollama"""
        logger.info("Converting to GGUF format for Ollama...")
        # This would require llama.cpp - simplified for now
        logger.info("GGUF conversion script would go here")
        logger.info("Run: python -m llama.cpp.convert --outtype q4_k_m output/")


# ============== RAG System Integration ==============
class MedicalRAGSystem:
    """RAG system for medical AI responses"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.ollama_client = None
        self.vector_store = None
        
    def initialize(self):
        """Initialize RAG system"""
        logger.info("Initializing Medical RAG System...")
        
        # Initialize vector store
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            
            self.vector_store = Chroma(
                persist_directory="./vector_db",
                embedding_function=embeddings
            )
            logger.info("Vector store initialized!")
        except Exception as e:
            logger.warning(f"Vector store initialization failed: {e}")
        
        return True
    
    def add_medical_data(self, data: List[Dict]):
        """Add medical data to vector store"""
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return
            
        # Create documents from data
        documents = []
        for item in data:
            doc = f"""
            Patient/Doctor: {item.get('name', '')}
            Information: {json.dumps(item, ensure_ascii=False)}
            """
            documents.append(doc)
        
        # Add to vector store
        self.vector_store.add_texts(documents)
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def query(self, question: str, k: int = 5) -> str:
        """Query the RAG system"""
        if not self.vector_store:
            return "RAG system not initialized"
        
        # Retrieve relevant documents
        docs = self.vector_store.similarity_search(question, k=k)
        
        # Format context
        context = "\n\n".join([d.page_content for d in docs])
        
        # Generate response using Ollama
        prompt = f"""Based on the following medical information, answer the question:

Context:
{context}

Question: {question}

Answer in Persian (Farsi) and be medically accurate:"""

        return prompt  # This would be sent to Ollama


# ============== Main Execution ==============
def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Gemma Medical Fine-tuning")
    parser.add_argument("--mode", choices=["prepare", "train", "convert", "all"], 
                       default="all", help="Execution mode")
    parser.add_argument("--data-dir", default="./data/medical", help="Data directory")
    args = parser.parse_args()
    
    # Create config
    config = Config()
    config.DATA_DIR = args.data_dir
    
    if args.mode in ["prepare", "all"]:
        # Prepare data
        logger.info("Preparing medical dataset...")
        processor = MedicalDataProcessor(config)
        
        # Create data directory structure
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
        # Create sample data files if they don't exist
        sample_patient = [{
            "record_number": "PR-001",
            "first_name": "علی",
            "last_name": "محمدی",
            "age": 45,
            "gender": "مرد",
            "blood_type": "O+",
            "allergies": "پنی‌سیلین",
            "chronic_diseases": "دیابت نوع 2",
            "medical_history": [
                "جراحی آپاندیس در سال 1395",
                "فشار خون بالا از سال 1398"
            ],
            "current_symptoms": [
                "سردرد",
                "خستگی مفرط",
                "تشنگی زیاد"
            ],
            "surgeries": "آپاندکتومی",
            "current_medications": "متformin 500mg"
        }]
        
        sample_doctor = [{
            "first_name": "سارا",
            "last_name": "احمدی",
            "specialty": "قلب و عروق",
            "education": "دکترای پزشکی از دانشگاه تهران",
            "years_experience": 15,
            "medical_license": "پ-12345"
        }]
        
        sample_kb = [{
            "name": "فشار خون بالا",
            "description": "فشار خون بالا یا هایپرتانسیون یکی از شایع‌ترین بیماری‌های قلبی عروقی است.",
            "symptoms": "سردرد، تنگی نفس، خونریزی بینی، سرگیجه",
            "treatment": "تغییر سبک زندگی، مصرف داروهای ضد فشار خون",
            "medications": "لوزارتان، آتنولول، هیدروکلروتیازید",
            "prevention": "کاهش نمک، ورزش منظم، کنترل استرس"
        }]
        
        sample_symptoms = [
            {"name": "سردرد", "possible_causes": ["میگرن", "فشار خون بالا", "استرس", "کم خوابی"]},
            {"name": "تنگی نفس", "possible_causes": ["آسم", "بیماری قلبی", "اضطراب", "کم خونی"]},
            {"name": "درد قفسه سینه", "possible_causes": ["حمله قلبی", "رفلاکس", "استرس", "آسیب عضلانی"]}
        ]
        
        # Save sample data
        with open(config.PATIENT_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(sample_patient, f, ensure_ascii=False, indent=2)
        with open(config.DOCTOR_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(sample_doctor, f, ensure_ascii=False, indent=2)
        with open(config.MEDICAL_KB_PATH, 'w', encoding='utf-8') as f:
            json.dump(sample_kb, f, ensure_ascii=False, indent=2)
        with open(config.SYMPTOMS_PATH, 'w', encoding='utf-8') as f:
            json.dump(sample_symptoms, f, ensure_ascii=False, indent=2)
        
        # Create instruction dataset
        dataset = processor.create_instruction_dataset()
        
        # Save training dataset
        train_data_path = f"{config.DATA_DIR}/train_dataset.json"
        processor.save_dataset(dataset, train_data_path)
        
        logger.info(f"Dataset preparation complete! {len(dataset)} examples created")
    
    if args.mode in ["train", "all"]:
        # Train model (requires transformers, peft, etc.)
        logger.info("Starting model training...")
        # This would require GPU and proper setup
        # trainer = GemmaFineTuner(config)
        # trainer.setup_model()
        # dataset = trainer.prepare_dataset(train_data_path)
        # trainer.train(dataset)
        # trainer.save_model()
        logger.info("Training requires GPU and additional setup")
    
    if args.mode in ["convert", "all"]:
        # Convert to GGUF
        logger.info("Model conversion would be done here")
        logger.info("Install llama.cpp and run conversion")
    
    logger.info("=" * 50)
    logger.info("GEMMA FINE-TUNING SETUP COMPLETE!")
    logger.info("=" * 50)
    logger.info(f"Data directory: {config.DATA_DIR}")
    logger.info(f"Output directory: {config.OUTPUT_DIR}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Download Gemma 2B model from HuggingFace")
    logger.info("2. Install required packages: pip install transformers peft bitsandbytes")
    logger.info("3. Run training: python finetune_gemma.py --mode train")
    logger.info("4. Convert to GGUF for Ollama")
    logger.info("5. Add to Ollama: ollama create gemma-medical")
    logger.info("6. Use in AI chat system")


if __name__ == "__main__":
    main()

