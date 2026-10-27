"""
Dataset schema definitions for EmbeddedCoder AI.
Strictly validates training examples, evaluation tasks, and benchmark items.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from embeddedcoder.core.constants import Subdomain, Architecture, HardwarePlatform, VerificationMethod


class TrainingExample(BaseModel):
    """Schema for a single training / instruction-response pair."""
    id: str = Field(..., description="Unique identifier, e.g. 'EC-EMB-001'")
    subdomain: Subdomain = Field(..., description="Target embedded engineering domain")
    platform: HardwarePlatform = Field(default=HardwarePlatform.UNIVERSAL)
    architecture: Architecture = Field(default=Architecture.GENERIC)
    language: str = Field(default="c", description="c, cpp, python, asm, or text")
    protocol_or_standard: Optional[str] = Field(None, description="e.g. Modbus, J1939, AIS-140")
    difficulty: str = Field(default="medium", description="beginner, intermediate, advanced, expert")
    verification_method: VerificationMethod = Field(default=VerificationMethod.UNIT_TEST)
    
    # Prompt and Response
    system_prompt: Optional[str] = Field(
        default="You are EmbeddedCoder AI, an expert embedded systems engineer. Provide technically precise, memory-safe, verifiable solutions.",
        description="System instruction for the model"
    )
    instruction: str = Field(..., min_length=10, description="The user query or engineering task")
    response: str = Field(..., min_length=10, description="The expert ground-truth answer or code")
    
    # Verifiable metadata & reference checks
    expected_output: Optional[str] = Field(None, description="Deterministic output or regex")
    test_harness_c: Optional[str] = Field(None, description="C unit test harness if applicable")
    test_vectors: Optional[List[Dict[str, Any]]] = Field(None, description="Protocol test vectors")
    known_limitations: Optional[str] = Field(None, description="Hardware constraints or edge cases")
    source_license: str = Field(default="Apache-2.0")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("ID must be at least 3 characters")
        return v.strip()


class BenchmarkItem(BaseModel):
    """Schema for a standardized held-out benchmark task."""
    id: str = Field(..., description="Benchmark task ID, e.g. 'BENCH-CRC-01'")
    category: str = Field(..., description="code_generation, debugging, protocol, rtos, linux, triage")
    subdomain: Subdomain
    platform: HardwarePlatform = Field(default=HardwarePlatform.UNIVERSAL)
    instruction: str = Field(..., min_length=10)
    ground_truth_reference: str = Field(..., min_length=5)
    verification_method: VerificationMethod
    verification_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data needed for automated verification: test vectors, golden CRC, or compiler code"
    )
