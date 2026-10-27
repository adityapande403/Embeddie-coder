"""
Configuration schemas for EmbeddedCoder AI pipelines.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
import yaml
from pathlib import Path


class ModelConfig(BaseModel):
    model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    torch_dtype: str = "bfloat16"
    load_in_4bit: bool = False
    device_map: str = "auto"
    max_length: int = 2048
    use_flash_attention: bool = False


class SFTConfig(BaseModel):
    model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    output_dir: str = "models/sft_checkpoint"
    dataset_path: str = "data/processed/train.jsonl"
    eval_dataset_path: str = "data/processed/val.jsonl"
    max_seq_length: int = 1536
    learning_rate: float = 2e-4
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 4
    num_train_epochs: int = 3
    warmup_ratio: float = 0.05
    weight_decay: float = 0.01
    logging_steps: int = 10
    save_strategy: str = "steps"
    save_steps: int = 100
    save_total_limit: int = 2
    fp16: bool = False
    bf16: bool = True
    seed: int = 42

    # LoRA settings
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = Field(
        default_factory=lambda: [
            "q_proj", "k_proj", "v_proj", "o_proj", 
            "gate_proj", "up_proj", "down_proj"
        ]
    )


class GRPOConfig(BaseModel):
    model_id: str = "models/sft_checkpoint"
    output_dir: str = "models/grpo_checkpoint"
    learning_rate: float = 5e-6
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    num_generations: int = 4
    max_completion_length: int = 512
    beta: float = 0.04


class ExportConfig(BaseModel):
    source_model_dir: str = "models/sft_checkpoint"
    output_merged_dir: str = "models/embeddedcoder_merged"
    output_gguf_dir: str = "models/gguf"
    quantization_formats: List[str] = Field(
        default_factory=lambda: ["Q4_K_M", "Q8_0"]
    )


def load_yaml_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
