"""
Standalone evaluation CLI script for EmbeddedCoder AI.
Evaluates base models, SFT checkpoints, or merged models on the held-out benchmark.
"""

import argparse
import json
from pathlib import Path
import torch
from peft import PeftModel
from embeddedcoder.inference.loader import load_model_and_tokenizer
from embeddedcoder.data.schema import BenchmarkItem
from embeddedcoder.evaluation.runner import BenchmarkRunner
from embeddedcoder.core.constants import EVAL_DATA_DIR, REPORTS_DIR


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate EmbeddedCoder AI model on held-out benchmarks")
    parser.add_argument(
        "--model_id", 
        type=str, 
        default="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        help="Base model ID or local directory"
    )
    parser.add_argument(
        "--adapter_path", 
        type=str, 
        default=None,
        help="Optional path to trained LoRA adapter weights"
    )
    parser.add_argument(
        "--benchmark_path", 
        type=str, 
        default=str(EVAL_DATA_DIR / "benchmark_suite.jsonl"),
        help="Path to benchmark JSONL"
    )
    parser.add_argument(
        "--report_name", 
        type=str, 
        default="baseline_evaluation",
        help="Output report filename stem"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 65)
    print(f"Evaluating Model: {args.model_id}")
    if args.adapter_path:
        print(f"With LoRA Adapter: {args.adapter_path}")
    print("=" * 65)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Model & Tokenizer
    print("\n[1/3] Loading model and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(
        model_id_or_path=args.model_id,
        device_map="auto"
    )

    if args.adapter_path:
        print(f"      Applying PEFT adapter from {args.adapter_path}...")
        model = PeftModel.from_pretrained(model, args.adapter_path)
        model.eval()

    # 2. Load Benchmark Items
    print("\n[2/3] Loading held-out benchmark items...")
    bench_items = []
    with open(args.benchmark_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                bench_items.append(BenchmarkItem(**json.loads(line)))
    print(f"      Loaded {len(bench_items)} held-out tasks.")

    # 3. Run Benchmark
    print("\n[3/3] Executing independent benchmark suite...")
    runner = BenchmarkRunner(model=model, tokenizer=tokenizer)
    summary = runner.run_suite(bench_items)

    # Output Summary
    print("\n" + "=" * 65)
    print(f"EVALUATION RESULTS: {args.report_name}")
    print("=" * 65)
    print(f"Total Tasks:          {summary['total_tasks']}")
    print(f"Passed Tasks:         {summary['passed_tasks']}")
    print(f"Overall Accuracy:     {summary['overall_accuracy_pct']:.1f}%")
    print(f"Average Latency:      {summary['avg_latency_ms']:.1f} ms/task")
    print("-" * 65)
    print(f"{'Category':<25} | {'Passed':<8} | {'Total':<6} | {'Accuracy':<8}")
    print("-" * 65)
    for cat, stats in summary["category_summary"].items():
        print(f"{cat:<25} | {stats['passed']:<8} | {stats['total']:<6} | {stats['accuracy']:<6.1f}%")
    print("=" * 65)

    # Save JSON Report
    json_path = REPORTS_DIR / f"{args.report_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Save Markdown Report
    md_path = REPORTS_DIR / f"{args.report_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Benchmark Evaluation Report: `{args.report_name}`\n\n")
        f.write(f"- **Model:** `{args.model_id}`\n")
        f.write(f"- **Adapter:** `{args.adapter_path or 'None (Base Model)'}`\n")
        f.write(f"- **Overall Accuracy:** `{summary['overall_accuracy_pct']}%`\n")
        f.write(f"- **Average Latency:** `{summary['avg_latency_ms']} ms`\n\n")
        f.write("## Category Performance\n\n")
        f.write("| Category | Passed | Total | Accuracy |\n")
        f.write("| :--- | :---: | :---: | :---: |\n")
        for cat, stats in summary["category_summary"].items():
            f.write(f"| {cat} | {stats['passed']} | {stats['total']} | {stats['accuracy']:.1f}% |\n")
        f.write("\n## Task Details\n\n")
        for res in summary["results"]:
            status = "✅ PASS" if res["passed"] else "❌ FAIL"
            f.write(f"### {res['id']}: {status}\n")
            f.write(f"- **Category:** `{res['category']}`\n")
            f.write(f"- **Method:** `{res['verification_method']}`\n")
            f.write(f"- **Latency:** `{res['latency_ms']:.1f} ms`\n\n")
            f.write(f"**Completion:**\n```\n{res['completion'][:400]}...\n```\n\n")

    print(f"\nSaved Reports to:\n  • {json_path}\n  • {md_path}\n")


if __name__ == "__main__":
    main()
