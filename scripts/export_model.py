"""
Model export and packaging engine for EmbeddedCoder AI.
Merges PEFT LoRA adapters with base model weights and generates Ollama Modelfile.
"""

import argparse
import json
import shutil
from pathlib import Path
import torch
from peft import PeftModel
from embeddedcoder.inference.loader import load_model_and_tokenizer
from embeddedcoder.core.constants import PROJECT_ROOT


def parse_args():
    parser = argparse.ArgumentParser(description="Merge and export EmbeddedCoder AI model for offline deployment")
    parser.add_argument(
        "--base_model_id", 
        type=str, 
        default="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        help="Base model ID"
    )
    parser.add_argument(
        "--adapter_dir", 
        type=str, 
        default="models/sft_checkpoint",
        help="Directory containing trained LoRA adapter"
    )
    parser.add_argument(
        "--output_dir", 
        type=str, 
        default="models/embeddedcoder_merged",
        help="Output directory for merged weights"
    )
    parser.add_argument(
        "--ollama_name", 
        type=str, 
        default="embeddedcoder:1.5b",
        help="Target Ollama model tag"
    )
    return parser.parse_args()


def export_model(base_model_id: str, adapter_dir: str, output_dir: str, ollama_name: str):
    print("=" * 65)
    print("EmbeddedCoder AI — Model Export & Release Packaging")
    print("=" * 65)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    adapter_path = Path(adapter_dir)

    # 1. Load Base Model and Tokenizer
    print("\n[1/4] Loading base model and tokenizer...")
    base_model, tokenizer = load_model_and_tokenizer(
        model_id_or_path=base_model_id,
        device_map="cpu", # Merge in system RAM to avoid VRAM overhead
        torch_dtype=torch.float32
    )

    # 2. Merge LoRA Adapter
    if adapter_path.exists() and (adapter_path / "adapter_model.safetensors").exists():
        print(f"\n[2/4] Merging LoRA adapter from {adapter_path} into base weights...")
        peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))
        merged_model = peft_model.merge_and_unload()
    else:
        print(f"\n[2/4] No adapter found at {adapter_path}. Exporting base model directly...")
        merged_model = base_model

    # 3. Save Merged Model & Tokenizer
    print(f"\n[3/4] Serializing merged weights to {out_path}...")
    merged_model.save_pretrained(str(out_path), safe_serialization=True)
    tokenizer.save_pretrained(str(out_path))

    # 4. Generate Ollama Modelfile
    print(f"\n[4/4] Generating Ollama Modelfile...")
    modelfile_path = out_path / "Modelfile"
    modelfile_content = f"""# EmbeddedCoder AI Ollama Modelfile
FROM {out_path.resolve()}

TEMPLATE \"\"\"<|im_start|>system
{{{{ .System }}}}<|im_end|>
<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
\"\"\"

SYSTEM \"\"\"You are EmbeddedCoder AI, an expert embedded systems engineer, firmware architect, compiler engineer, and protocol specialist. Prioritize technical correctness, memory safety, hardware timing, and verifiable facts over speculation.\"\"\"

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
PARAMETER temperature 0.1
PARAMETER top_p 0.95
"""
    modelfile_path.write_text(modelfile_content, encoding="utf-8")

    # Export Manifest
    manifest = {
        "model_name": "EmbeddedCoder AI",
        "codename": "EmbeddedCoder-1.5B",
        "version": "0.1.0",
        "base_model": base_model_id,
        "adapter_source": adapter_dir,
        "format": "safetensors",
        "precision": "fp32_merged",
        "ollama_modelfile": str(modelfile_path),
        "license": "Apache-2.0"
    }
    manifest_path = out_path / "model_export_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 65)
    print("Export Complete:")
    print(f"  • Merged Directory:   {out_path}")
    print(f"  • Ollama Modelfile:   {modelfile_path}")
    print(f"  • Export Manifest:    {manifest_path}")
    print("=" * 65)


def main():
    args = parse_args()
    export_model(
        base_model_id=args.base_model_id,
        adapter_dir=args.adapter_dir,
        output_dir=args.output_dir,
        ollama_name=args.ollama_name
    )


if __name__ == "__main__":
    main()
