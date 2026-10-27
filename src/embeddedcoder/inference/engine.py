"""
Public-facing Python SDK interface for EmbeddedCoder AI.
Provides local, privacy-first embedded engineering inference.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Union
import torch
from peft import PeftModel
from embeddedcoder.inference.loader import load_model_and_tokenizer
from embeddedcoder.protocols.modbus import ModbusRTU
from embeddedcoder.protocols.can import CANFrame
from embeddedcoder.protocols.telematics import AIS140Packet
from embeddedcoder.protocols.crc import crc16_modbus


class EmbeddedCoder:
    """
    High-level Python SDK for EmbeddedCoder AI.
    
    Usage:
        assistant = EmbeddedCoder(model_path="models/sft_checkpoint", offline=True)
        response = assistant.debug(platform="stm32", language="c", logs="CFSR = 0x00008200")
    """

    def __init__(
        self,
        model_path: str = "models/sft_checkpoint",
        base_model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        offline: bool = True,
        device: Optional[str] = None,
    ):
        self.model_path = model_path
        self.base_model_id = base_model_id
        self.offline = offline

        # Determine device
        if device is None:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load model and tokenizer
        path = Path(model_path)
        if path.exists() and (path / "adapter_config.json").exists():
            # Load base model + LoRA adapter
            base_model, self.tokenizer = load_model_and_tokenizer(
                model_id_or_path=base_model_id,
                device_map=self.device
            )
            self.model = PeftModel.from_pretrained(base_model, str(path))
        else:
            # Load standalone or merged model
            target = str(path) if path.exists() else base_model_id
            self.model, self.tokenizer = load_model_and_tokenizer(
                model_id_or_path=target,
                device_map=self.device
            )

        self.model.eval()

    def ask(
        self,
        prompt: str,
        system_prompt: str = "You are EmbeddedCoder AI, an expert embedded systems engineer. Provide technically precise, memory-safe, verifiable solutions.",
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        """General inquiry or engineering prompt."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        if hasattr(self.tokenizer, "apply_chat_template"):
            formatted = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            formatted = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

        inputs = self.tokenizer(formatted, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            output_tokens = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=(temperature > 0.0),
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        new_tokens = output_tokens[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    def generate_code(
        self,
        prompt: str,
        platform: str = "generic_cortex_m",
        language: str = "c",
    ) -> str:
        """Generate platform-specific, memory-conscious embedded code."""
        query = f"Target Platform: {platform}\nLanguage: {language}\nRequirement: {prompt}\nWrite production-grade, memory-safe code."
        return self.ask(query)

    def debug(
        self,
        platform: str = "generic_embedded_linux",
        language: str = "c",
        logs: Optional[str] = None,
        code: Optional[str] = None,
    ) -> str:
        """Diagnose firmware failures from crash logs, traces, or faulty code."""
        parts = [f"Target Platform: {platform}", f"Language: {language}"]
        if logs:
            parts.append(f"Observed Logs / Crash Dump:\n{logs}")
        if code:
            parts.append(f"Faulty Code:\n{code}")
        parts.append("Perform systematic root-cause diagnosis. Differentiate observed evidence from plausible causes and specify verification steps.")
        
        query = "\n\n".join(parts)
        return self.ask(query)

    def decode_packet(self, protocol: str, hex_bytes: str) -> Dict[str, Any]:
        """
        Decode a binary packet using deterministic protocol decoders with LLM explanation.
        """
        clean_hex = hex_bytes.strip().replace(" ", "").replace("0x", "")
        raw_bytes = bytes.fromhex(clean_hex)
        prot_lower = protocol.lower()

        structured: Dict[str, Any] = {}
        if "modbus" in prot_lower:
            structured = ModbusRTU.parse_frame(raw_bytes)
        elif "j1939" in prot_lower or "can" in prot_lower:
            if len(raw_bytes) == 4:
                can_id = int.from_bytes(raw_bytes, "big")
                structured = CANFrame.decode_j1939_can_id(can_id)
            else:
                structured = CANFrame.decode_obd2_payload(raw_bytes)
        elif "ais140" in prot_lower or "ais-140" in prot_lower:
            try:
                text = raw_bytes.decode("ascii", errors="ignore")
                structured = AIS140Packet.parse_packet(text)
            except Exception as e:
                structured = {"error": str(e)}

        # Explain via LLM
        prompt = f"Explain this decoded {protocol} packet: {structured}. Highlight any anomalies or protocol parameters."
        explanation = self.ask(prompt)

        return {
            "protocol": protocol,
            "raw_hex": clean_hex.upper(),
            "deterministic_fields": structured,
            "ai_explanation": explanation
        }
