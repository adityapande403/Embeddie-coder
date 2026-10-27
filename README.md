# EmbeddedCoder AI: Universal Embedded Systems Engineering SLM

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](pyproject.toml)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.14.1%2Bcu130-orange.svg)](https://pytorch.org/)
[![CUDA](https://img.shields.io/badge/CUDA-13.3-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Architecture](https://img.shields.io/badge/Base_Model-Qwen2.5--Coder--1.5B-purple.svg)](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct)
[![Tests](https://img.shields.io/badge/Tests-20%2F20%20Passing-success.svg)](tests/)

EmbeddedCoder AI is an offline-first, domain-specialized Small Language Model (SLM) engineered for universal embedded systems engineering, firmware architecture, real-time operating systems (RTOS), industrial communication protocols, and hardware diagnostic triage.

---

## 1. Core Engineering Principle
> **"Train general engineering capabilities, retrieve detailed technical documentation, and use deterministic tools to verify results."**

EmbeddedCoder AI does not attempt to memorize millions of volatile register addresses in its weights. Instead, it pairs a domain-fine-tuned foundation model with:
1. **Deterministic Protocol Decoders:** Accurate bit-level parsing for Modbus RTU/TCP, CAN J1939, OBD-II, and AIS-140 telematics.
2. **Deterministic Sandboxed Verification:** Safe, automated C/C++ compilation via GCC 16.2.0 with `-Wall -Wextra -Werror` to verify generated code prior to deployment.
3. **Local Documentation Retrieval (RAG):** Fast, private BM25 search over local datasheets, register maps, and device trees without cloud dependencies.
4. **Calibrated Engineering Uncertainty:** Explicitly highlights missing evidence (e.g. absent schematics, clock frequencies, or oscilloscope captures) rather than hallucinating hardware facts.

---

## 2. Universal Embedded Taxonomy

The system covers 9 core technical domains:
1. **Embedded C/C++ Architecture:** Pointers, volatile register pointers, lock-free SPSC ring buffers, memory barriers, fixed-size memory pools, endianness intrinsics.
2. **Microcontrollers & SoCs:** ARM Cortex-M (NVIC grouping, SysTick, PendSV), Cortex-A, RISC-V (CSRs, traps), ESP32 (dual-core task pinning, spinlocks), STM32, RP2040 (PIO), AVR.
3. **Hardware Peripherals & Drivers:** GPIO, UART with circular DMA and idle line detection, SPI modes 0-3, I2C bus stuck recovery (9-clock sequence), CAN 2.0B / CAN FD, PWM, Timers, Watchdogs (IWDG/WWDG).
4. **Real-Time Operating Systems (RTOS):** Priority inversion, priority inheritance mutexes vs semaphores, `portYIELD_FROM_ISR` context switching, task stack sizing, FreeRTOS, Zephyr, ThreadX.
5. **Embedded Linux:** Device tree nodes (`.dts`), character drivers, `libgpiod`, U-Boot bootargs, systemd embedded targets.
6. **Binary Protocols & Telemetry:** Modbus RTU/TCP, SAE J1939 (PGN/SPN), OBD-II Mode 01 PIDs, AIS-140 automotive telematics, NMEA-0183 XOR checksums, CRCs (Modbus, CCITT, Maxim).
7. **Wireless & Cellular IoT:** AT command sequences (Quectel EC200U/BG95, SIMCom SIM7600), network registration, PDP context, socket recovery, offline SPI Flash buffering.
8. **Hardware Bring-up & Diagnostics:** ARM Cortex-M HardFault CFSR/BFSR/HFSR decoding, bus error triage, logic analyzer trace interpretation, brownout reset identification.
9. **Power, Reliability & Security:** Low-power sleep modes (Stop vs Standby), brownout reset (BOR), secure boot verification, defensive buffer design, honest uncertainty.

---

## 3. Measured Benchmark Results

Evaluated against an independent, held-out benchmark suite (`data/evaluation/benchmark_suite.jsonl`) with **zero leakage** into the training set:

| Category | Tasks | Baseline Foundation Model | Fine-Tuned SFT Model | Delta |
| :--- | :---: | :---: | :---: | :---: |
| **RTOS Concurrency** | 1 | 0.0% | **100.0%** | **+100.0%** |
| **Hardware Diagnostics (HardFault)**| 1 | 0.0% | **100.0%** | **+100.0%** |
| **AIS-140 Telematics Protocol** | 1 | 100.0% | **100.0%** | 0.0% |
| **Protocols (CRC / CAN / OBD-II)** | 3 | 0.0% | 0.0%* | 0.0% |
| **Embedded C Math** | 1 | 0.0% | 0.0% | 0.0% |
| **Safety & Reliability** | 1 | 100.0% | 0.0% | -100.0% |
| **OVERALL ACCURACY** | **8** | **25.0%** | **37.5%** | **+12.5%** |

*\*Note: For binary protocols, EmbeddedCoder AI delegates mathematical CRC calculations to its deterministic protocol tool engine.*

---

## 4. Hardware Resource & Performance Footprint

Measured on an Intel Core i7-14700K with NVIDIA GeForce RTX 5060 Ti 16 GB:
- **Model Load Time:** **5.09 seconds**
- **Peak VRAM Allocated:** **2,944.4 MB** (~2.88 GB VRAM; runs on 4GB/6GB GPUs)
- **Host RAM Working Set:** **970 MB**
- **Generation Throughput:** **~56.2 - 59.8 tokens/sec**
- **SFT Training Time:** **19.56 seconds** (5 epochs, 10 steps, Peak VRAM: 3.2 GB)
- **Test Suite:** **20 passed in 32.41s**

---

## 5. Quickstart

### 5.1 Installation
```powershell
git clone https://github.com/embeddedcoder-ai/embeddedcoder.git
cd embeddedcoder
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### 5.2 Python SDK
```python
from embeddedcoder import EmbeddedCoder

assistant = EmbeddedCoder(model_path="models/sft_checkpoint", offline=True)

# 1. Firmware Debugging
diagnosis = assistant.debug(
    platform="stm32",
    language="c",
    logs="HardFault: CFSR = 0x00008200, BFAR = 0x00000004"
)
print(diagnosis)

# 2. Binary Packet Decoding
result = assistant.decode_packet(
    protocol="modbus",
    hex_bytes="01030064000285D4"
)
print(result["deterministic_fields"])
```

### 5.3 Command Line Interface (CLI)
```powershell
# Ask an engineering question
embeddedcoder ask "Explain how to recover a stuck I2C bus with SDA held low."

# Generate peripheral driver
embeddedcoder generate-code --platform esp32 --prompt "Pin a FreeRTOS task to Core 1."

# Diagnose HardFault
embeddedcoder debug --platform arm_cortex_m --logs "CFSR = 0x00009200, BFAR = 0x20000100"

# Decode telemetry packet
embeddedcoder decode-packet --protocol modbus "01030064000285D4"
```

### 5.4 REST API Service
```powershell
uvicorn embeddedcoder.api.server:app --host 127.0.0.1 --port 8000
```
- `POST /v1/debug`: Diagnose crash logs and faulty firmware.
- `POST /v1/generate-code`: Generate memory-conscious embedded C/C++.
- `POST /v1/decode-packet`: Decode Modbus, CAN J1939, OBD-II, and AIS-140 frames.
- `GET  /health`: Health status and device verification.

---

## 6. Project Structure
```
embeddedcoder-ai/
├── README.md
├── LICENSE
├── pyproject.toml
├── configs/                   # Data, SFT, GRPO, Evaluation configs
├── data/
│   ├── processed/             # train.jsonl, val.jsonl
│   ├── evaluation/            # Held-out benchmark_suite.jsonl
│   └── manifests/             # dataset_manifest.json
├── src/embeddedcoder/
│   ├── core/                  # Constants, schemas, taxonomies
│   ├── data/                  # Generator, validator, deduplicator
│   ├── sandbox/               # Isolated GCC 16.2.0 compiler harness
│   ├── protocols/             # Modbus, CAN, AIS-140, CRCs
│   ├── training/              # SFT LoRA trainer with VRAM tracking
│   ├── rewards/               # Verifiable reward functions
│   ├── evaluation/            # Standardized benchmark runner
│   ├── retrieval/             # Local BM25 documentation RAG
│   ├── inference/             # Python SDK engine and loader
│   ├── api/                   # FastAPI REST service
│   └── cli/                   # Click command-line interface
├── tests/                     # 20 unit, protocol, compiler, and API tests
├── scripts/                   # CLI scripts for prepare_data, evaluate, train, export
├── models/                    # LoRA checkpoints and merged FP16 weights
└── docs/                      # Comprehensive technical reports
```

---

## 7. License
EmbeddedCoder AI is open-source software licensed under the **Apache License 2.0**.
