# EmbeddedCoder AI: Reproduction Guide

Follow these exact steps to reproduce the dataset preparation, baseline evaluation, SFT domain fine-tuning, benchmark evaluation, model export, and local inference on Windows or Linux.

---

## 1. Environment Setup

### 1.1 Clone / Navigate to Workspace
```powershell
cd d:\Aditya\hf4
```

### 1.2 Virtual Environment & Dependencies
```powershell
# Create virtual environment
py -3.10 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install package dependencies
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install transformers peft trl accelerate datasets fastapi uvicorn click rich pytest
pip install -e .
```

### 1.3 Ensure Storage Isolation
Set `HF_HOME` to ensure caches do not fill up the system `C:` drive:
```powershell
$env:HF_HOME = "d:\Aditya\hf4\.cache\huggingface"
```

---

## 2. Dataset Curation & Contamination Checks
Generate the multi-domain training corpus and held-out benchmark suite, run deduplication, and execute leakage checks:
```powershell
python scripts\prepare_data.py
```
*Expected Output:* Validates 15 domain examples, 8 benchmark tasks, and reports `Zero leakage detected`.

---

## 3. Run Automated Test Suite
Run all unit, protocol, compiler sandbox, and integration tests:
```powershell
python -m pytest -v
```
*Expected Output:* `20 passed in ~32s`.

---

## 4. Evaluate Baseline Foundation Model
Run the benchmark suite on the unmodified base model:
```powershell
python scripts\evaluate.py --model_id "Qwen/Qwen2.5-Coder-1.5B-Instruct" --report_name "baseline_foundation_evaluation"
```
*Expected Output:* Baseline Accuracy **25.0%**. Reports saved to `artifacts/reports/baseline_foundation_evaluation.md`.

---

## 5. Domain SFT Training
Execute domain fine-tuning using LoRA:
```powershell
python scripts\train_sft.py --config configs\sft.yaml --epochs 5
```
*Expected Output:* Trains for 10 steps in ~20 seconds on an RTX 5060 Ti with ~3.2 GB peak VRAM. Saves adapter to `models/sft_checkpoint/`.

---

## 6. Evaluate Trained SFT Model
Run the benchmark suite on the fine-tuned model checkpoint:
```powershell
python scripts\evaluate.py --model_id "Qwen/Qwen2.5-Coder-1.5B-Instruct" --adapter_path "models/sft_checkpoint" --report_name "sft_model_evaluation"
```
*Expected Output:* SFT Accuracy **37.5%** (+12.5% gain). RTOS concurrency and HardFault diagnosis jump to **100%**.

---

## 7. Model Export & Ollama Packaging
Merge LoRA weights with base weights and generate the Ollama Modelfile:
```powershell
python scripts\export_model.py --base_model_id "Qwen/Qwen2.5-Coder-1.5B-Instruct" --adapter_dir "models/sft_checkpoint" --output_dir "models/embeddedcoder_merged"
```
*Expected Output:* Saves standalone `model.safetensors` and `Modelfile`.

---

## 8. Run Inference

### 8.1 Via CLI
```powershell
# General inquiry
python -m embeddedcoder.cli.main ask "Explain how to recover a stuck I2C bus with SDA held low."

# Firmware code generation
python -m embeddedcoder.cli.main generate-code --platform stm32 --prompt "Write an interrupt-safe SPSC ring buffer in C."

# Diagnostic triage
python -m embeddedcoder.cli.main debug --platform arm_cortex_m --logs "CFSR = 0x00008200, BFAR = 0x00000004"

# Packet decoding
python -m embeddedcoder.cli.main decode-packet --protocol modbus --hex-bytes "01030064000285D4"
```

### 8.2 Via Python SDK
```python
from embeddedcoder import EmbeddedCoder

assistant = EmbeddedCoder(model_path="models/sft_checkpoint", offline=True)
res = assistant.debug(
    platform="stm32",
    language="c",
    logs="HardFault: CFSR = 0x00008200, BFAR = 0x00000004"
)
print(res)
```

### 8.3 Via REST API
```powershell
uvicorn embeddedcoder.api.server:app --host 127.0.0.1 --port 8000
```
Then send requests to `http://127.0.0.1:8000/v1/debug` or `http://127.0.0.1:8000/v1/decode-packet`.
