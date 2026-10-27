"""
Model and tokenizer loading utilities for EmbeddedCoder AI.
Ensures caches are pinned to high-capacity storage and manages device placement.
"""

import os
import torch
from pathlib import Path
from typing import Tuple, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, PreTrainedModel, PreTrainedTokenizer
from embeddedcoder.core.constants import HF_CACHE_DIR

# Enforce cache location
os.environ["HF_HOME"] = str(HF_CACHE_DIR)


def get_optimal_device() -> torch.device:
    """Return cuda if available, else cpu."""
    if torch.cuda.is_available():
        return torch.device("cuda:0")
    return torch.device("cpu")


def get_optimal_dtype() -> torch.dtype:
    """Return bfloat16 if cuda supports it, else float16 or float32."""
    if torch.cuda.is_available():
        if torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16
    return torch.float32


def load_tokenizer(model_id_or_path: str) -> PreTrainedTokenizer:
    """Load and configure the Hugging Face tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(
        model_id_or_path,
        cache_dir=str(HF_CACHE_DIR),
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def load_model(
    model_id_or_path: str,
    device_map: str = "auto",
    torch_dtype: Optional[torch.dtype] = None,
    load_in_4bit: bool = False,
) -> PreTrainedModel:
    """Load model with optimal precision and device placement."""
    if torch_dtype is None:
        torch_dtype = get_optimal_dtype()

    kwargs = {
        "cache_dir": str(HF_CACHE_DIR),
        "torch_dtype": torch_dtype,
        "trust_remote_code": True,
    }

    if torch.cuda.is_available():
        kwargs["device_map"] = device_map

    if load_in_4bit:
        kwargs["load_in_4bit"] = True

    model = AutoModelForCausalLM.from_pretrained(
        model_id_or_path,
        **kwargs
    )
    model.eval()
    return model


def load_model_and_tokenizer(
    model_id_or_path: str,
    device_map: str = "auto",
    torch_dtype: Optional[torch.dtype] = None,
    load_in_4bit: bool = False,
) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """Convenience helper to load both model and tokenizer."""
    tokenizer = load_tokenizer(model_id_or_path)
    model = load_model(
        model_id_or_path,
        device_map=device_map,
        torch_dtype=torch_dtype,
        load_in_4bit=load_in_4bit
    )
    return model, tokenizer
