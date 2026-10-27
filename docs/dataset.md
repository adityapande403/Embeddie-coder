# EmbeddedCoder AI: Dataset Engineering Report

---

## 1. Dataset Design & Taxonomy

The EmbeddedCoder training corpus is systematically partitioned across nine universal embedded systems engineering subdomains:

| Subdomain | Description | Hardware Focus |
| :--- | :--- | :--- |
| **`embedded_c_cpp`** | Memory safety, pointers, volatile registers, ring buffers, memory barriers, fixed-block allocators, endianness intrinsics. | Universal / ANSI C99 / C++17 |
| **`mcus_socs`** | NVIC priority grouping, SysTick, CSR registers, dual-core task pinning, clock trees, spinlocks. | ARM Cortex-M, Cortex-A, RISC-V, ESP32, STM32, RP2040 |
| **`peripherals_drivers`** | GPIO, UART+DMA, SPI modes 0-3, I2C bus stuck recovery (9-clock pulse), CAN 2.0B/FD, Timers, Watchdogs (IWDG/WWDG). | Hardware Peripherals |
| **`rtos_concurrency`** | Priority inversion, mutexes vs semaphores, `FromISR` context switching, task stack sizing, event groups. | FreeRTOS, Zephyr, ThreadX |
| **`embedded_linux`** | Device trees (`.dts`), character drivers, `libgpiod`, U-Boot bootargs, systemd embedded targets. | Linux SoC / SBCs |
| **`protocols_telemetry`** | Modbus RTU/TCP, CAN J1939 (PGN/SPN), OBD-II Mode 01 PIDs, AIS-140 telematics, NMEA-0183 XOR checksums, CRCs. | Industrial & Automotive Protocols |
| **`wireless_iot`** | Cellular AT commands (Quectel EC200U/BG95, SIMCom SIM7600), network registration, PDP context, socket recovery, offline flash buffering. | 4G/LTE-M/NB-IoT Modules |
| **`hardware_diagnostics`** | ARM Cortex-M HardFault CFSR/BFSR/MMFSR decoding, logic analyzer traces, brownout detection, memory leak isolation. | Hardware Triage & Logic Analyzers |
| **`power_security`** | Low-power sleep modes (Stop vs Standby), brownout reset (BOR), secure boot verification, honest uncertainty when evidence is insufficient. | Battery & Security Systems |

---

## 2. Quality Control & Contamination Prevention

### 2.1 Deduplication
- **Exact Duplicate Detection:** Normalized MD5 hashing on input instructions eliminated identical requests.
- **Near-Duplicate Detection:** Word 3-gram Jaccard similarity with a threshold of 0.75 pruned redundant phrasing.

### 2.2 Leakage & Contamination Elimination
- Training examples and held-out benchmark items were evaluated using `DataValidator.check_evaluation_leakage()`.
- **Result:** **0 leakage violations** detected between the training set and the held-out benchmark suite.
- Held-out benchmark items utilize independent test vectors, differing payloads, and distinct engineering scenarios not present in the training set.

### 2.3 Subdomain Balance
Distribution across subdomains in `data/manifests/dataset_manifest.json`:
- `embedded_c_cpp`: 4 examples
- `mcus_socs`: 2 examples
- `protocols_telemetry`: 2 examples
- `power_security`: 2 examples
- `peripherals_drivers`: 1 example
- `rtos_concurrency`: 1 example
- `embedded_linux`: 1 example
- `wireless_iot`: 1 example
- `hardware_diagnostics`: 1 example

---

## 3. Provenance & Licensing
All synthetic and rule-based engineering patterns in this dataset were authored specifically for EmbeddedCoder AI under the **Apache-2.0** license. No proprietary, NDAd, or confidential vendor datasheets were ingested.
