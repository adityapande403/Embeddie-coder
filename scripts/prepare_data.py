"""
Data preparation, validation, deduplication, and leakage-checking script.
Produces validated train.jsonl, val.jsonl, benchmark_suite.jsonl, and dataset_manifest.json.
"""

import json
import random
from pathlib import Path
from embeddedcoder.core.constants import (
    PROCESSED_DATA_DIR, EVAL_DATA_DIR, MANIFESTS_DIR
)
from embeddedcoder.data.generator import EmbeddedDataGenerator
from embeddedcoder.data.validator import DataValidator
from embeddedcoder.evaluation.benchmark_suite import get_held_out_benchmark_suite


def main():
    print("=" * 60)
    print("EmbeddedCoder AI — Data Curation & Validation Engine")
    print("=" * 60)

    # Ensure output directories exist
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate Raw Dataset
    print("\n[1/5] Generating multi-domain training candidates...")
    raw_candidates = EmbeddedDataGenerator.generate_all()
    print(f"      Total candidates generated: {len(raw_candidates)}")

    # 2. Schema Validation and Deduplication
    print("\n[2/5] Running schema validation and near-duplicate deduplication...")
    valid_examples, rejected = DataValidator.validate_and_deduplicate(
        raw_candidates, similarity_threshold=0.85
    )
    print(f"      Valid unique examples retained: {len(valid_examples)}")
    print(f"      Rejected / duplicate records:   {len(rejected)}")

    # 3. Generate Benchmark Suite
    print("\n[3/5] Generating held-out benchmark suite...")
    benchmarks = get_held_out_benchmark_suite()
    print(f"      Held-out benchmark items:       {len(benchmarks)}")

    # 4. Leakage & Contamination Check
    print("\n[4/5] Executing train-evaluation contamination & leakage detection...")
    leakage = DataValidator.check_evaluation_leakage(valid_examples, benchmarks, leakage_threshold=0.70)
    if leakage:
        print(f"      WARNING: {len(leakage)} potential leakage violations detected!")
        for leak in leakage:
            print(f"      -> Train {leak['train_id']} leaks Bench {leak['benchmark_id']} (sim: {leak['similarity']:.2f})")
    else:
        print("      SUCCESS: Zero leakage detected between training and benchmark splits!")

    # 5. Split and Save Datasets
    print("\n[5/5] Splitting and serializing datasets...")
    random.seed(42)
    shuffled = list(valid_examples)
    random.shuffle(shuffled)

    val_count = max(1, int(len(shuffled) * 0.15))
    train_split = shuffled[val_count:]
    val_split = shuffled[:val_count]

    train_path = PROCESSED_DATA_DIR / "train.jsonl"
    val_path = PROCESSED_DATA_DIR / "val.jsonl"
    bench_path = EVAL_DATA_DIR / "benchmark_suite.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for ex in train_split:
            f.write(json.dumps(ex.model_dump(), ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for ex in val_split:
            f.write(json.dumps(ex.model_dump(), ensure_ascii=False) + "\n")

    with open(bench_path, "w", encoding="utf-8") as f:
        for bm in benchmarks:
            f.write(json.dumps(bm.model_dump(), ensure_ascii=False) + "\n")

    # Generate Manifest
    dist = DataValidator.get_subdomain_distribution(valid_examples)
    manifest = {
        "version": "1.0.0",
        "total_examples": len(valid_examples),
        "train_count": len(train_split),
        "val_count": len(val_split),
        "benchmark_count": len(benchmarks),
        "subdomain_distribution": dist,
        "leakage_violations": len(leakage),
        "train_path": str(train_path),
        "val_path": str(val_path),
        "benchmark_path": str(bench_path)
    }

    manifest_path = MANIFESTS_DIR / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 60)
    print("Dataset Preparation Summary:")
    print(f"  • Training Examples:    {len(train_split)} ({train_path})")
    print(f"  • Validation Examples:  {len(val_split)} ({val_path})")
    print(f"  • Benchmark Suite:      {len(benchmarks)} ({bench_path})")
    print(f"  • Manifest Saved:       {manifest_path}")
    print("\nSubdomain Distribution:")
    for k, v in dist.items():
        print(f"  - {k:<25}: {v} examples")
    print("=" * 60)


if __name__ == "__main__":
    main()
