"""
Deterministic, verifiable reward functions for embedded systems engineering and GRPO alignment.
Scores completions based on objective compilation, CRC accuracy, and protocol compliance.
"""

import re
from typing import List, Dict, Any, Optional
from embeddedcoder.sandbox.compiler import SandboxCompiler
from embeddedcoder.protocols.crc import crc16_modbus, nmea_checksum


class VerifiableRewardEngine:
    def __init__(self, compiler: Optional[SandboxCompiler] = None):
        self.compiler = compiler or SandboxCompiler()

    def compilation_reward(self, completions: List[str], **kwargs) -> List[float]:
        """Reward function: 1.0 if generated C/C++ code compiles with -Wall -Wextra -Werror, 0.0 otherwise."""
        rewards = []
        for text in completions:
            match = re.search(r"```(?:c|cpp)?\n(.*?)```", text, re.DOTALL)
            code = match.group(1).strip() if match else ""
            if not code or len(code) < 15:
                rewards.append(0.0)
                continue

            res = self.compiler.compile_and_run(code, is_cpp="std::" in code, run_binary=False)
            rewards.append(1.0 if res.success else 0.0)
        return rewards

    def crc_accuracy_reward(self, completions: List[str], expected_crcs: List[str], **kwargs) -> List[float]:
        """Reward function: 1.0 if completion contains the exact hexadecimal or integer CRC."""
        rewards = []
        for text, exp in zip(completions, expected_crcs):
            clean_text = text.lower()
            clean_exp = exp.lower()
            if clean_exp in clean_text:
                rewards.append(1.0)
            elif clean_exp.startswith("0x") and clean_exp[2:] in clean_text:
                rewards.append(1.0)
            else:
                rewards.append(0.0)
        return rewards

    def protocol_field_reward(
        self, 
        completions: List[str], 
        expected_fields: List[Dict[str, Any]], 
        **kwargs
    ) -> List[float]:
        """Reward function: ratio of correctly extracted/constructed protocol fields."""
        rewards = []
        for text, fields in zip(completions, expected_fields):
            if not fields:
                rewards.append(1.0)
                continue

            matches = 0
            for k, v in fields.items():
                val_str = str(v).lower()
                if len(val_str) > 1 and val_str in text.lower():
                    matches += 1
            score = matches / len(fields)
            rewards.append(float(score))
        return rewards

    def honest_uncertainty_reward(self, completions: List[str], is_uncertain: List[bool], **kwargs) -> List[float]:
        """Reward function: 1.0 if completion correctly acknowledges missing engineering evidence."""
        rewards = []
        triggers = [
            "cannot determine", "insufficient evidence", "schematic",
            "hardware issue", "oscilloscope", "not possible to know",
            "missing information", "voltage droop", "pull-up", "miso"
        ]
        for text, should_be_uncertain in zip(completions, is_uncertain):
            found_uncertainty = any(t in text.lower() for t in triggers)
            if should_be_uncertain:
                rewards.append(1.0 if found_uncertainty else 0.0)
            else:
                rewards.append(0.0 if found_uncertainty else 1.0)
        return rewards
