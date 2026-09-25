import os
import torch
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    pipeline
)
from peft import LoraConfig, PeftModel
from trl import SFTTrainer

# 1. Configuration
base_model_name = "google/gemma-2-2b-it" # or 9b if resources allow
new_model_name = "gemma-2-2b-heart-disease"
output_dir = "./results_gemma"

# 2. BitsAndBytes configuration (Quantization)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=False,
)

# 3. Load Model and Tokenizer
device_map = {"": 0} # Put on GPU 0

model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    quantization_config=bnb_config,
    device_map=device_map,
    trust_remote_code=True
)
model.config.use_cache = False
model.config.pretraining_tp = 1

tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# 4. Prepare Dataset (Heart Disease)
# Assuming a CSV with columns: age, sex, chest_pain, rest_bp, cholesterol, fasting_bs, rest_ecg, max_hr, exercise_angina, old_peak, st_slope, heart_disease
def prepare_data(csv_path):
    df = pd.read_csv(csv_path)
    
    # Create instruction-tuning style prompts
    def format_row(row):
        instruction = "You are a medical AI assistant specializing in cardiology. Based on the following patient data, analyze the risk of heart disease."
        input_data = (
            f"Age: {row['Age']}, Sex: {row['Sex']}, Chest Pain: {row['ChestPainType']}, "
            f"Resting BP: {row['RestingBP']}, Cholesterol: {row['Cholesterol']}, "
            f"Fasting BS: {row['FastingBS']}, Resting ECG: {row['RestingECG']}, "
            f"Max HR: {row['MaxHR']}, Exercise Angina: {row['ExerciseAngina']}, "
            f"Old Peak: {row['OldPeak']}, ST Slope: {row['ST_Slope']}"
        )
        response = f"Analysis: The patient has a {'high' if row['HeartDisease'] == 1 else 'low'} risk of heart disease based on the provided metrics. [Detailed medical explanation would go here]"
        
        # Gemma instruction format
        return f"<start_of_turn>user\n{instruction}\n\nPatient Data: {input_data}<end_of_turn>\n<start_of_turn>model\n{response}<end_of_turn>"

    df['text'] = df.apply(format_row, axis=1)
    dataset = Dataset.from_pandas(df[['text']])
    return dataset

# Note: User needs to provide the heart.csv file from Kaggle
# dataset = prepare_data("heart.csv")

# 5. LoRA Configuration
peft_config = LoraConfig(
    lora_alpha=16,
    lora_dropout=0.1,
    r=64,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj"] # Gemma specific modules
)

# 6. Training Arguments
training_arguments = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=1,
    optim="paged_adamw_32bit",
    save_steps=25,
    logging_steps=25,
    learning_rate=2e-4,
    weight_decay=0.001,
    fp16=False,
    bf16=False,
    max_grad_norm=0.3,
    max_steps=-1,
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="constant",
    report_to="tensorboard"
)

# 7. SFT Trainer
# trainer = SFTTrainer(
#     model=model,
#     train_dataset=dataset,
#     peft_config=peft_config,
#     dataset_text_field="text",
#     max_seq_length=None,
#     tokenizer=tokenizer,
#     args=training_arguments,
#     packing=False,
# )

# 8. Train and Save
# trainer.train()
# trainer.model.save_pretrained(new_model_name)

print(f"Fine-tuning script for {base_model_name} initialized. Please provide heart.csv and uncomment training lines to start.")
