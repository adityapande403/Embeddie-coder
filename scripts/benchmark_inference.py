"""
Inference performance, latency, and memory benchmarking script for EmbeddedCoder AI.
Profiles token generation throughput, latency to first token, peak VRAM, and RAM usage.
"""

import argparse
import json
import time
from pathlib import Path
import psutil
import torch
from embeddedcoder.inference.loader import load_model_and_tokenizer
from embeddedcoder.core.constants import REPORTS_DIR


def parse_args():
    parser = argparse.ArgumentParser(description="Profile inference speed, latency, and VRAM")
    parser.add_argument(
        "--model_path", 
        type=str, 
        default="models/embeddedcoder_merged",
        help="Path to merged model or base model"
    )
    parser.add_argument("--num_runs", type=int, default=3, help="Number of profiling repetitions")
    return parser.parse_args()


def benchmark_model(model_path: str, num_runs: int = 3):
    print("=" * 65)
    print(f"Benchmarking Inference Performance: {model_path}")
    print("=" * 65)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Measure RAM before loading
    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    # 1. Load Model
    start_load = time.perf_counter()
    model, tokenizer = load_model_and_tokenizer(model_path, device_map="auto")
    load_time_sec = time.perf_counter() - start_load

    ram_after_mb = process.memory_info().rss / (1024 * 1024)
    vram_alloc_mb = (torch.cuda.memory_allocated() / (1024 * 1024)) if torch.cuda.is_available() else 0.0

    print(f"Load Time:        {load_time_sec:.2f} s")
    print(f"Host RAM Usage:   {ram_after_mb - ram_before_mb:.1f} MB (Total process: {ram_after_mb:.1f} MB)")
    print(f"GPU VRAM Usage:   {vram_alloc_mb:.1f} MB")

    # 2. Benchmark Queries
    test_prompts = [
        ("Short (Driver Init)", "Write a C function to initialize STM32 GPIO pin PA5 as a push-pull output."),
        ("Medium (Protocol Parse)", "Explain the Modbus RTU Function Code 0x03 packet structure and implement the CRC check in C."),
        ("Long (RTOS Architecture)", "Design a complete FreeRTOS task architecture with priority inheritance mutexes and ISR queue passing for a high-reliability IoT telemetry device.")
    ]

    results = []

    for label, prompt in test_prompts:
        print(f"\nEvaluating: {label}...")
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        input_len = inputs["input_ids"].shape[1]

        throughputs = []
        latencies = []
        generated_lens = []

        for r in range(num_runs):
            if torch.cuda.is_available():
                torch.cuda.synchronize()

            t0 = time.perf_counter()
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id
                )

            if torch.cuda.is_available():
                torch.cuda.synchronize()

            t1 = time.perf_counter()
            total_time = t1 - t0
            output_tokens = outputs[0][input_len:]
            num_tokens = len(output_tokens)
            tok_per_sec = num_tokens / total_time if total_time > 0 else 0.0

            throughputs.append(tok_per_sec)
            latencies.append(total_time)
            generated_lens.append(num_tokens)

        avg_tps = sum(throughputs) / len(throughputs)
        avg_lat = sum(latencies) / len(latencies)
        avg_tokens = sum(generated_lens) / len(generated_lens)

        print(f"  • Avg Throughput:  {avg_tps:.1f} tokens/sec")
        print(f"  • Avg Latency:     {avg_lat * 1000.0:.1f} ms for {avg_tokens:.0f} tokens")

        results.append({
            "prompt_type": label,
            "input_tokens": input_len,
            "output_tokens": avg_tokens,
            "avg_throughput_tps": round(avg_tps, 1),
            "avg_latency_ms": round(avg_lat * 1000.0, 1),
        })

    report = {
        "model_path": model_path,
        "load_time_seconds": round(load_time_sec, 2),
        "vram_allocated_mb": round(vram_alloc_mb, 1),
        "host_ram_used_mb": round(ram_after_mb - ram_before_mb, 1),
        "benchmarks": results
    }

    report_json_path = REPORTS_DIR / "inference_performance_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    report_md_path = REPORTS_DIR / "inference_performance_report.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# Inference Performance & Memory Profiling Report\n\n")
        f.write(f"- **Evaluated Checkpoint:** `{model_path}`\n")
        f.write(f"- **Model Load Duration:** `{load_time_sec:.2f} s`\n")
        f.write(f"- **VRAM Allocation:** `{vram_alloc_mb:.1f} MB`\n")
        f.write(f"- **Host RAM Working Set:** `{ram_after_mb:.1f} MB`\n\n")
        f.write("## Generation Throughput & Latency\n\n")
        f.write("| Prompt Complexity | Input Tokens | Generated Tokens | Throughput (tok/s) | Latency (ms) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")
        for r in results:
            f.write(f"| {r['prompt_type']} | {r['input_tokens']} | {r['output_tokens']:.0f} | **{r['avg_throughput_tps']}** | {r['avg_latency_ms']} |\n")

    print(f"\nPerformance report saved to:\n  • {report_json_path}\n  • {report_md_path}\n")


def main():
    args = parse_args()
    benchmark_model(args.model_path, args.num_runs)


if __name__ == "__main__":
    main()
