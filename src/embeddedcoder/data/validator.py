"""
Data validation, deduplication, and train-eval leakage detection engine.
"""

import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from embeddedcoder.data.schema import TrainingExample, BenchmarkItem
from embeddedcoder.core.constants import Subdomain


class DataValidator:
    @staticmethod
    def compute_hash(text: str) -> str:
        """Normalized MD5 hash for exact duplicate detection."""
        normalized = " ".join(text.strip().lower().split())
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def get_ngrams(text: str, n: int = 3) -> Set[str]:
        """Extract word n-grams (default 3-gram) for leakage and near-duplicate analysis."""
        words = text.strip().lower().split()
        if len(words) < n:
            return {" ".join(words)}
        return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}

    @staticmethod
    def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
        """Calculate Jaccard similarity between two n-gram sets."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return float(intersection) / float(union) if union > 0 else 0.0

    @classmethod
    def validate_and_deduplicate(
        cls, 
        examples: List[Dict[str, Any]], 
        similarity_threshold: float = 0.85
    ) -> Tuple[List[TrainingExample], List[Dict[str, Any]]]:
        """
        Validate records against schema and remove exact and near-duplicates.
        Returns: (valid_unique_examples, rejected_records)
        """
        valid_examples: List[TrainingExample] = []
        rejected: List[Dict[str, Any]] = []
        seen_hashes: Set[str] = set()
        seen_ngram_pools: List[Tuple[str, Set[str]]] = []

        for item in examples:
            try:
                example = TrainingExample(**item)
            except Exception as e:
                rejected.append({"item": item, "reason": f"Schema validation error: {str(e)}"})
                continue

            # Exact duplicate check on instruction
            inst_hash = cls.compute_hash(example.instruction)
            if inst_hash in seen_hashes:
                rejected.append({"item": item, "reason": "Exact duplicate instruction detected"})
                continue

            # Near-duplicate check
            ngrams = cls.get_ngrams(example.instruction, n=3)
            is_near_dup = False
            for existing_id, existing_ngrams in seen_ngram_pools:
                sim = cls.calculate_jaccard_similarity(ngrams, existing_ngrams)
                if sim >= similarity_threshold:
                    rejected.append({
                        "item": item, 
                        "reason": f"Near-duplicate of {existing_id} (Jaccard similarity: {sim:.2f})"
                    })
                    is_near_dup = True
                    break

            if not is_near_dup:
                seen_hashes.add(inst_hash)
                seen_ngram_pools.append((example.id, ngrams))
                valid_examples.append(example)

        return valid_examples, rejected

    @classmethod
    def check_evaluation_leakage(
        cls,
        training_examples: List[TrainingExample],
        benchmark_items: List[BenchmarkItem],
        leakage_threshold: float = 0.50
    ) -> List[Dict[str, Any]]:
        """
        Check for contaminated training examples that leak benchmark questions or test vectors.
        """
        leakage_violations: List[Dict[str, Any]] = []

        bench_ngrams = [
            (b.id, cls.get_ngrams(b.instruction, n=3), b.instruction)
            for b in benchmark_items
        ]

        for train_ex in training_examples:
            train_ngrams = cls.get_ngrams(train_ex.instruction, n=3)
            for bench_id, b_ngrams, b_inst in bench_ngrams:
                sim = cls.calculate_jaccard_similarity(train_ngrams, b_ngrams)
                if sim >= leakage_threshold:
                    leakage_violations.append({
                        "train_id": train_ex.id,
                        "benchmark_id": bench_id,
                        "similarity": sim,
                        "train_instruction": train_ex.instruction[:80],
                        "bench_instruction": b_inst[:80]
                    })

        return leakage_violations

    @staticmethod
    def get_subdomain_distribution(examples: List[TrainingExample]) -> Dict[str, int]:
        """Compute the count of examples per subdomain."""
        counts = {s.value: 0 for s in Subdomain}
        for ex in examples:
            counts[ex.subdomain.value] = counts.get(ex.subdomain.value, 0) + 1
        return counts
