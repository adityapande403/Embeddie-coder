# EmbeddedCoder AI: Architecture Report
**Universal Embedded Systems Engineering Small Language Model**

---

## 1. System Overview

EmbeddedCoder AI is an offline-first, domain-specialized Small Language Model (SLM) engineered to assist firmware architects, embedded software engineers, and hardware bring-up teams. The core design principle is:
> **Train general engineering capabilities, retrieve detailed technical documentation, and use deterministic tools to verify results.**

```mermaid
graph TD
    subgraph Local_Inference_Pipeline [Local Privacy-First Inference]
        USER[Developer / Engineer] --> CLI[CLI / REST API / Python SDK]
        CLI --> RAG[Local BM25 / Chunked RAG Engine]
        RAG --> LLM[EmbeddedCoder Merged Model (FP16 / Ollama)]
        LLM --> PROTO_DEC[Deterministic Protocol Decoders]
        PROTO_DEC --> SANDBOX[Sandboxed GCC 16.2.0 Verification]
        SANDBOX --> RESP[Structured, Verified Response]
    end
```

---

## 2. Component Architecture

### 2.1 Core Subsystems
1. **Foundation Model Layer (`src/embeddedcoder/inference/loader.py`):**
   - Base Model: `Qwen/Qwen2.5-Coder-1.5B-Instruct`
   - Parameters: 1.54 Billion
   - Architecture: Dense Decoder-only Transformer with RoPE, SwiGLU, RMSNorm, and Grouped Query Attention (GQA).
   - Context Window: 32,768 tokens native.
   - Cache Management: Hugging Face home pinned to `D:\Aditya\hf4\.cache\huggingface` to prevent system drive space exhaustion.

2. **Deterministic Protocol Verification Engine (`src/embeddedcoder/protocols/`):**
   - High-precision bit-level parsers and builders for:
     - **Modbus RTU & TCP:** Function Codes 0x03, 0x04, 0x06, 0x10 with 16-bit CRC-16 IBM verification.
     - **SAE J1939 & CAN 2.0B:** 29-bit CAN identifier deconstruction (Priority, PGN, Source Address).
     - **SAE J1979 / OBD-II:** Diagnostic Mode 01 PID extraction (Engine RPM, Speed, Coolant Temp).
     - **AIS-140 Telematics:** Standard Indian automotive telematics framing, GPS coordinate extraction, ignition status, emergency alert bits, and NMEA XOR checksum verification.
     - **CRCs & Checksums:** CRC-16 Modbus (0xA001), CRC-16 CCITT (0x1021), CRC-8 Maxim Dallas 1-Wire (0x8C).

3. **Compiler Sandbox (`src/embeddedcoder/sandbox/compiler.py`):**
   - Isolated GCC 16.2.0 / G++ portable toolchain (`w64devkit`).
   - Compilation flags: `-O2 -Wall -Wextra -Werror -std=c11` (or `-std=c++17`).
   - Strict warning enforcement: Any unused variable, implicit type conversion, or uninitialized read triggers an immediate compilation failure.
   - Process time limit (5.0s compilation, 3.0s execution) to prevent infinite loops during control algorithm tests.

4. **Local Retrieval Engine (`src/embeddedcoder/retrieval/rag.py`):**
   - Inverted BM25 documentation index with TF-IDF cosine ranking.
   - Extracts section-level passages from `.h`, `.c`, `.dts`, `.txt`, and `.md` technical manuals.
   - Injects verifiable citation headers (`[Doc: <ID> | File: <Path>:<Lines> | Section: <Section>]`).

5. **Application Interfaces:**
   - **Python SDK (`src/embeddedcoder/inference/engine.py`):** Native `EmbeddedCoder` class for programmatic firmware debugging and code generation.
   - **FastAPI REST API (`src/embeddedcoder/api/server.py`):** Localhost HTTP endpoints (`/v1/debug`, `/v1/generate-code`, `/v1/decode-packet`, `/v1/explain-log`, `/health`, `/v1/model-info`).
   - **Developer CLI (`src/embeddedcoder/cli/main.py`):** Terminal utility providing `ask`, `debug`, `generate-code`, `decode-packet`, and `info`.
