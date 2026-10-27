"""
Domain-specific Supervised Fine-Tuning (SFT) training engine for EmbeddedCoder AI.
Configures LoRA adapters, conversational formatting, hardware memory management, and checkpoints.
"""

import json
import os
import torch
from pathlib import Path
from typing import Dict, Any, List, Optional
from datasets import Dataset
from transformers import (
    TrainingArguments,
    TrainerCallback,
    PreTrainedModel,
    PreTrainedTokenizer,
    TrainerControl,
    TrainerState,
)
from trl import SFTTrainer
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from embeddedcoder.inference.loader import load_model_and_tokenizer
from embeddedcoder.core.config import SFTConfig
from embeddedcoder.core.constants import HF_CACHE_DIR

# Ensure HF cache is pinned to D: drive
os.environ["HF_HOME"] = str(HF_CACHE_DIR)


class MemoryTrackingCallback(TrainerCallback):
    """Logs GPU VRAM allocation at each step."""
    def on_step_end(self, args, state: TrainerState, control: TrainerControl, **kwargs):
        if torch.cuda.is_available() and state.global_step % 5 == 0:
            alloc_mb = torch.cuda.memory_allocated() / (1024 * 1024)
            res_mb = torch.cuda.memory_reserved() / (1024 * 1024)
            print(f" [Step {state.global_step}] VRAM Allocated: {alloc_mb:.1f} MB | Reserved: {res_mb:.1f} MB")


def prepare_dataset_for_sft(jsonl_path: Path, tokenizer: PreTrainedTokenizer) -> Dataset:
    """Load JSONL dataset and format into chat conversation templates."""
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            
            # Format as standard conversational messages
            system_msg = item.get("system_prompt", "You are EmbeddedCoder AI, an expert embedded systems engineer.")
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": item["instruction"]},
                {"role": "assistant", "content": item["response"]}
            ]
            
            # Render chat template
            if hasattr(tokenizer, "apply_chat_template"):
                text = tokenizer.apply_chat_template(messages, tokenize=False)
            else:
                text = f"<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n{item['instruction']}<|im_end|>\n<|im_start|>assistant\n{item['response']}<|im_end|>"
            
            records.append({"text": text})

    return Dataset.from_list(records)


def train_sft(config: SFTConfig) -> str:
    """Execute domain supervised fine-tuning and save best checkpoint."""
    print("=" * 65)
    print(f"Starting SFT Training for: {config.model_id}")
    print(f"Output Directory:          {config.output_dir}")
    print(f"Dataset Path:              {config.dataset_path}")
    print("=" * 65)

    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Load Model and Tokenizer
    print("\n[1/4] Loading base model and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(
        model_id_or_path=config.model_id,
        device_map="auto"
    )

    # 2. Configure LoRA
    if config.use_lora:
        print("\n[2/4] Setting up PEFT LoRA adapter...")
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            target_modules=config.target_modules,
            bias="none"
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

    # Enable gradient checkpointing to reduce VRAM
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()

    # 3. Prepare Datasets
    print("\n[3/4] Tokenizing and formatting datasets...")
    train_dataset = prepare_dataset_for_sft(Path(config.dataset_path), tokenizer)
    eval_dataset = None
    if config.eval_dataset_path and Path(config.eval_dataset_path).exists():
        eval_dataset = prepare_dataset_for_sft(Path(config.eval_dataset_path), tokenizer)
    print(f"      Train samples: {len(train_dataset)}")
    if eval_dataset:
        print(f"      Validation samples: {len(eval_dataset)}")

    from trl import SFTConfig as TRLSFTConfig

    # 4. Training Arguments
    sft_args = TRLSFTConfig(
        output_dir=str(output_path),
        dataset_text_field="text",
        max_length=config.max_seq_length,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        weight_decay=config.weight_decay,
        warmup_steps=5,
        num_train_epochs=config.num_train_epochs,
        logging_steps=config.logging_steps,
        save_strategy=config.save_strategy,
        save_steps=config.save_steps,
        save_total_limit=config.save_total_limit,
        fp16=config.fp16,
        bf16=config.bf16 if torch.cuda.is_bf16_supported() else False,
        seed=config.seed,
        report_to="none",
        eval_strategy="no" if eval_dataset is None else "steps",
        eval_steps=config.save_steps if eval_dataset is not None else None,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        callbacks=[MemoryTrackingCallback()]
    )

    # Check for existing checkpoint recovery
    last_checkpoint = None
    if output_path.exists():
        checkpoints = [d for d in output_path.glob("checkpoint-*") if d.is_dir()]
        if checkpoints:
            last_checkpoint = str(sorted(checkpoints, key=lambda x: int(x.name.split("-")[1]))[-1])
            print(f"\nFound existing checkpoint. Resuming from: {last_checkpoint}")

    print("\n[4/4] Executing SFT optimization loop...")
    train_result = trainer.train(resume_from_checkpoint=last_checkpoint)
    print(f"\nTraining completed. Loss: {train_result.training_loss:.4f}")

    # Save final adapter and tokenizer
    print(f"\nSaving fine-tuned adapter to {output_path}...")
    trainer.save_model(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    # Save training metrics
    metrics_path = output_path / "training_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "training_loss": train_result.training_loss,
            "train_runtime_seconds": train_result.metrics.get("train_runtime", 0),
            "train_samples_per_second": train_result.metrics.get("train_samples_per_second", 0),
            "global_step": train_result.global_step,
            "config": config.model_dump()
        }, f, indent=2)

    print(f"Metrics saved to {metrics_path}")
    return str(output_path)
