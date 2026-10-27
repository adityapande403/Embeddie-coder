# Model Card: EmbeddedCoder AI (1.5B)

---

## 1. Model Details
- **Model Name:** EmbeddedCoder AI
- **Codename:** `EmbeddedCoder-1.5B`
- **Architecture:** Causal Language Model (Transformer Decoder with RoPE, GQA, SwiGLU, RMSNorm)
- **Base Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
- **Parameters:** 1.54 Billion
- **Context Window:** 32,768 tokens native (expandable to 128k via YaRN)
- **Primary Languages:** C (C99/C11), C++ (C++17), Python, Device Tree (.dts), Assembly, English
- **License:** Apache-2.0
- **Release Version:** 0.1.0

---

## 2. Intended Use Cases
### Primary Applications:
- **Firmware Development:** Generating memory-safe, portable embedded C/C++ drivers, ring buffers, and fixed-block memory allocators.
- **Hardware Peripherals:** Configuring GPIO, UART with circular DMA, SPI modes 0-3, I2C bus recovery routines, and CAN acceptance filters.
- **Real-Time Concurrency:** Designing FreeRTOS, Zephyr, and ThreadX task architectures, preventing priority inversion, and implementing ISR-safe queues.
- **Protocol Engineering:** Parsing, constructing, and validating industrial and telematics packets (Modbus RTU/TCP, CAN J1939, OBD-II, AIS-140, NMEA-0183).
- **Diagnostic Triage:** Analyzing ARM Cortex-M HardFault crash dumps (`CFSR`, `HFSR`, `BFAR`), bus faults, brownout reset flags, and logic analyzer traces.
- **Technical Documentation Assistance:** Grounding firmware design in local technical documentation via local BM25 RAG.

---

## 3. Limitations & Out-of-Scope Uses
### Technical Limitations:
1. **Mathematical CRC Computation:** Like most language models, EmbeddedCoder AI should not be relied upon to mentally calculate 16-bit polynomial CRCs in free text without the integrated deterministic tool engine. Always use the built-in `decode_packet` protocol tool.
2. **Missing Evidence:** The model cannot deduce physical pin assignments, clock frequencies, or proprietary vendor registers if they are not provided in the prompt or indexed technical documentation.
3. **No Direct Hardware Flashing:** EmbeddedCoder AI generates code and diagnostic steps; it does not automatically flash microcontrollers or manipulate hardware pins directly.

### Out-of-Scope / Prohibited Uses:
- Do not use for automated deployment in active life-critical medical devices or nuclear control systems without rigorous human verification, formal code analysis, and hardware-in-the-loop (HIL) testing.
- Bypassing device security protections, cryptographic signing, or automotive safety fail-safes.
