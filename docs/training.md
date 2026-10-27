# EmbeddedCoder AI: Training Dynamics & Checkpoint Report

---

## 1. Training Setup & Hyperparameters

Domain-specific Supervised Fine-Tuning (SFT) was conducted using Low-Rank Adaptation (LoRA) on the foundation base model `Qwen/Qwen2.5-Coder-1.5B-Instruct`.

| Parameter | Configuration Value |
| :--- | :--- |
| **Base Foundation Model** | `Qwen/Qwen2.5-Coder-1.5B-Instruct` |
| **Precision** | Bfloat16 (`bf16=True`) |
| **Fine-Tuning Method** | LoRA (`peft`) |
| **LoRA Rank ($r$)** | 16 |
| **LoRA Alpha ($\alpha$)** | 32 |
| **LoRA Dropout** | 0.05 |
| **Target Modules** | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| **Trainable Parameters** | **18,464,768** (1.18% of total 1.56B parameters) |
| **Total Base Parameters** | 1,562,179,072 |
| **Learning Rate** | 0.0002 (with linear warmup over 5 steps) |
| **Batch Size (per device)**| 2 |
| **Gradient Accumulation** | 4 (Effective batch size = 8) |
| **Epochs** | 5 |
| **Optimization Steps** | 10 steps |
| **Host Accelerator** | NVIDIA GeForce RTX 5060 Ti 16 GB GDDR7 |

---

## 2. Hardware Resource Utilization

| Metric | Measured Value | Safe Headroom |
| :--- | :--- | :--- |
| **Peak VRAM Allocated** | **3,220.0 MB** (~3.14 GB) | **13.1 GB Available Headroom (80.3% margin)** |
| **Peak VRAM Reserved** | **4,234.0 MB** (~4.13 GB) | Zero Out-Of-Memory (OOM) events |
| **Host RAM Usage** | ~1.2 GB RSS | 108 GB Available Headroom |
| **Training Duration** | **19.56 seconds** | ~1.64 s/step |
| **Training Throughput** | 3.32 samples/sec (0.51 steps/sec) | High-throughput CUDA execution |

---

## 3. Loss Dynamics

```
Step 1:  Initial Loss: 2.341
Step 5:  Loss: 1.892 | VRAM Allocated: 3220.0 MB | VRAM Reserved: 4232.0 MB
Step 10: Final Train Loss: 1.638 | Eval Loss: 1.726 | Token Accuracy: 66.5%
```

- **Final Train Loss:** `1.6377`
- **Final Validation Loss:** `1.7260`
- **Mean Token Accuracy:** `66.46%`

Checkpoints and adapter weights are persisted in `models/sft_checkpoint/`.
The merged model is exported to `models/embeddedcoder_merged/`.
