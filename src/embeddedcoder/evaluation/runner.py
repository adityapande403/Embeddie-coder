"""
Independent evaluation harness for EmbeddedCoder AI.
Evaluates foundation models, SFT checkpoints, and quantized exports on the held-out benchmark suite.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer
from embeddedcoder.data.schema import BenchmarkItem
from embeddedcoder.core.constants import VerificationMethod
from embeddedcoder.sandbox.compiler import SandboxCompiler


class BenchmarkRunner:
    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        compiler: Optional[SandboxCompiler] = None,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.compiler = compiler or SandboxCompiler()

    def generate_completion(
        self,
        instruction: str,
        system_prompt: str = "You are EmbeddedCoder AI, an expert embedded systems engineer. Provide technically precise, memory-safe, verifiable solutions.",
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        """Generate response from model using the standard chat template."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction}
        ]

        if hasattr(self.tokenizer, "apply_chat_template"):
            prompt_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            prompt_text = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"

        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=(temperature > 0.0),
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        completion = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        return completion

    def evaluate_task(self, item: BenchmarkItem) -> Dict[str, Any]:
        """Run single benchmark task and verify the output."""
        start_time = time.perf_counter()
        completion = self.generate_completion(item.instruction)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        is_passed = False
        details: Dict[str, Any] = {}

        if item.verification_method == VerificationMethod.GCC_COMPILATION:
            # Extract C/C++ code from triple backticks
            code_match = re.search(r"```(?:c|cpp)?\n(.*?)```", completion, re.DOTALL)
            extracted_code = code_match.group(1).strip() if code_match else completion
            res = self.compiler.compile_and_run(extracted_code, is_cpp="std::" in extracted_code)
            
            expected_out = item.verification_payload.get("expected_output")
            if res.success:
                if expected_out:
                    is_passed = expected_out.lower() in res.execution_stdout.lower()
                else:
                    is_passed = True
            details = {
                "compile_success": res.success,
                "compile_exit_code": res.exit_code,
                "execution_stdout": res.execution_stdout[:200],
                "compile_stderr": res.stderr[:200]
            }

        elif item.verification_method == VerificationMethod.CRC_VERIFICATION:
            expected_hex = item.verification_payload.get("expected_crc_hex", "").lower()
            expected_int = item.verification_payload.get("expected_crc_int")
            clean_comp = completion.lower()
            
            hex_match = expected_hex in clean_comp or (expected_hex[2:] in clean_comp if expected_hex.startswith("0x") else False)
            int_match = str(expected_int) in clean_comp if expected_int else False
            is_passed = hex_match or int_match
            details = {"expected": expected_hex, "found_in_text": is_passed}

        elif item.verification_method == VerificationMethod.GOLDEN_PACKET_DECODE:
            # Check presence of expected key telemetry fields
            payload = item.verification_payload
            match_count = 0
            check_keys = []
            for k, v in payload.items():
                val_str = str(v).lower()
                if len(val_str) > 1 and val_str in completion.lower():
                    match_count += 1
                check_keys.append(k)
            
            is_passed = (match_count >= max(1, len(check_keys) // 2))
            details = {"matches": match_count, "total_keys": len(check_keys)}

        elif item.verification_method == VerificationMethod.DIAGNOSTIC_TRIAGE:
            root_cause = item.verification_payload.get("root_cause", "").lower()
            keywords = [w for w in root_cause.split() if len(w) > 3]
            match_count = sum(1 for kw in keywords if kw in completion.lower())
            is_passed = (match_count >= max(1, len(keywords) // 2)) or ("stack" in completion.lower() and "fault" in completion.lower())
            details = {"matched_keywords": match_count, "target_keywords": keywords}

        elif item.verification_method == VerificationMethod.HONEST_UNCERTAINTY:
            # Check if model refuses to fabricate and states that evidence is insufficient
            uncertainty_phrases = [
                "cannot determine", "insufficient evidence", "schematic",
                "hardware issue", "oscilloscope", "not possible to know",
                "missing information", "voltage droop", "pull-up", "miso"
            ]
            is_passed = any(p in completion.lower() for p in uncertainty_phrases)
            details = {"recognized_uncertainty": is_passed}

        elif item.verification_method == VerificationMethod.UNIT_TEST:
            kw = item.verification_payload.get("expected_keyword", "").lower()
            is_passed = kw in completion.lower()
            details = {"found_keyword": is_passed}

        return {
            "id": item.id,
            "category": item.category,
            "subdomain": item.subdomain.value,
            "passed": is_passed,
            "verification_method": item.verification_method.value,
            "latency_ms": latency_ms,
            "completion": completion,
            "details": details
        }

    def run_suite(self, benchmark_items: List[BenchmarkItem]) -> Dict[str, Any]:
        """Evaluate entire benchmark suite and aggregate metrics."""
        results = []
        passed_count = 0
        latencies = []

        by_category: Dict[str, Dict[str, int]] = {}

        for item in benchmark_items:
            res = self.evaluate_task(item)
            results.append(res)
            latencies.append(res["latency_ms"])
            if res["passed"]:
                passed_count += 1

            cat = item.category
            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0}
            by_category[cat]["total"] += 1
            if res["passed"]:
                by_category[cat]["passed"] += 1

        total = len(benchmark_items)
        pass_rate = (passed_count / total * 100.0) if total > 0 else 0.0
        avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

        category_summary = {}
        for cat, stats in by_category.items():
            category_summary[cat] = {
                "total": stats["total"],
                "passed": stats["passed"],
                "accuracy": (stats["passed"] / stats["total"] * 100.0) if stats["total"] > 0 else 0.0
            }

        return {
            "total_tasks": total,
            "passed_tasks": passed_count,
            "overall_accuracy_pct": round(pass_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "category_summary": category_summary,
            "results": results
        }
