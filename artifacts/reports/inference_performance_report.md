# Inference Performance & Memory Profiling Report

- **Evaluated Checkpoint:** `models/embeddedcoder_merged`
- **Model Load Duration:** `5.09 s`
- **VRAM Allocation:** `2944.4 MB`
- **Host RAM Working Set:** `970.0 MB`

## Generation Throughput & Latency

| Prompt Complexity | Input Tokens | Generated Tokens | Throughput (tok/s) | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Short (Driver Init) | 20 | 256 | **56.2** | 4571.4 |
| Medium (Protocol Parse) | 24 | 256 | **59.6** | 4297.8 |
| Long (RTOS Architecture) | 26 | 256 | **59.8** | 4282.5 |
