"""
Unit tests for data schema validation, deduplication, and leakage detection.
"""

import pytest
from embeddedcoder.data.schema import TrainingExample, BenchmarkItem
from embeddedcoder.data.validator import DataValidator
from embeddedcoder.core.constants import Subdomain, HardwarePlatform, VerificationMethod


def test_schema_valid_example():
    ex = TrainingExample(
        id="EC-TEST-001",
        subdomain=Subdomain.EMBEDDED_C_CPP,
        platform=HardwarePlatform.UNIVERSAL,
        instruction="Explain the difference between volatile and non-volatile pointers.",
        response="Volatile tells the compiler that the value may change outside program flow."
    )
    assert ex.id == "EC-TEST-001"
    assert ex.subdomain == Subdomain.EMBEDDED_C_CPP


def test_schema_invalid_id():
    with pytest.raises(ValueError):
        TrainingExample(
            id="  ",  # Too short / whitespace
            subdomain=Subdomain.EMBEDDED_C_CPP,
            instruction="Some instruction text here",
            response="Some response text here"
        )


def test_deduplication_exact_and_near():
    raw = [
        {
            "id": "EC-1",
            "subdomain": "embedded_c_cpp",
            "instruction": "Explain how volatile pointers work in embedded C firmware programming.",
            "response": "Volatile pointers prevent register caching."
        },
        {
            "id": "EC-2",
            "subdomain": "embedded_c_cpp",
            "instruction": "Explain how volatile pointers work in embedded C firmware programming.",  # Exact duplicate
            "response": "Different text."
        },
        {
            "id": "EC-3",
            "subdomain": "embedded_c_cpp",
            "instruction": "Explain how volatile pointers work in embedded C firmware systems.",  # Near duplicate
            "response": "Different text."
        },
        {
            "id": "EC-4",
            "subdomain": "peripherals_drivers",
            "instruction": "How to configure hardware PWM on an STM32 timer?",  # Unique
            "response": "Configure CCR and ARR registers."
        }
    ]
    valid, rejected = DataValidator.validate_and_deduplicate(raw, similarity_threshold=0.75)
    assert len(valid) == 2  # EC-1 and EC-4 retained
    assert len(rejected) == 2  # EC-2 (exact) and EC-3 (near) rejected


def test_leakage_detection():
    train_ex = [
        TrainingExample(
            id="TRAIN-01",
            subdomain=Subdomain.PROTOCOLS_TELEMETRY,
            instruction="Calculate the 16-bit CRC-16 Modbus (IBM) checksum for hex payload 020400080002.",
            response="CRC is 0x7230"
        )
    ]
    bench_item = [
        BenchmarkItem(
            id="BENCH-01",
            category="protocol",
            subdomain=Subdomain.PROTOCOLS_TELEMETRY,
            instruction="Calculate the 16-bit CRC-16 Modbus (IBM) checksum for the following hex payload: 020400080002.",
            ground_truth_reference="0x7230",
            verification_method=VerificationMethod.CRC_VERIFICATION
        )
    ]
    violations = DataValidator.check_evaluation_leakage(train_ex, bench_item, leakage_threshold=0.40)
    assert len(violations) == 1
    assert violations[0]["train_id"] == "TRAIN-01"
    assert violations[0]["benchmark_id"] == "BENCH-01"
