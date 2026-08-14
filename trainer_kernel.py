# ==============================================================================
# AUTONOMOUS LORA FINE-TUNER (RUNS ON KAGGLE T4 GPU)
# ==============================================================================
import os
import json
import torch
from datasets import Dataset
from huggingface_hub import HfApi
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# Environment variables injected during execution
HF_TOKEN = os.environ.get("HF_TOKEN")
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"
OUTPUT_MODEL_REPO = "Kumar5674/kalyan-kishore-lora-v2"

hf_api = HfApi(token=HF_TOKEN)

print("📦 Fetching verified training trajectories from Hugging Face Vault...")
files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
json_files = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]

training_samples = []
for f_path in json_files:
    try:
        local_p = hf_api.hf_hub_download(repo_id=VAULT_REPO, filename=f_path, repo_type="model")
        with open(local_p, "r") as f:
            data = json.load(f)
        code_solution = data.get("solution_code") or data.get("code", "")
        if data.get("reward", 0.0) > 0.0 and len(code_solution) > 40:
            training_samples.append({
                "instruction": f"Implement a verified, deterministic solution with strict assertions for: {data.get('domain', 'general algorithmic problem')}.",
                "output": code_solution
            })
    except Exception:
        continue

print(f"✅ Extracted {len(training_samples)} gold-standard training samples.")

# Format as ChatML Alpaca dataset
formatted_data = [
    {"text": f"<|im_start|>user\n{s['instruction']}<|im_end|>\n<|im_start|>assistant\n```python\n{s['output']}\n```<|im_end|>"}
    for s in training_samples
]
dataset = Dataset.from_list(formatted_data)

# Load base model in 4-bit precision
max_seq_length = 2048
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-Coder-3B-Instruct-bnb-4bit",
    max_seq_length=max_seq_length,
    load_in_4bit=True
)

# Apply LoRA target adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth"
)

# Configure trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=50,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=5,
        output_dir="kalyan_kishore_checkpoints"
    )
)

print("⚡ Starting LoRA fine-tuning...")
trainer.train()

# Push fine-tuned adapter weights to Hugging Face
print("🚀 Pushing updated weights to Hugging Face...")
model.push_to_hub_merged(
    OUTPUT_MODEL_REPO,
    tokenizer,
    save_method="lora",
    token=HF_TOKEN
)

# Record training watermark
watermark_payload = {
    "total_trained_samples": len(training_samples),
    "model_version": "v2-lora",
    "status": "completed"
}
with open("training_watermark.json", "w") as f:
    json.dump(watermark_payload, f, indent=2)

hf_api.upload_file(
    path_or_fileobj="training_watermark.json",
    path_in_repo="training_watermark.json",
    repo_id=VAULT_REPO,
    repo_type="model"
)
print("🎉 Autonomous training complete and checkpoint published!")
