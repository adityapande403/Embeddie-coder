"""
FastAPI REST API server for EmbeddedCoder AI.
Provides local, privacy-first endpoints for debugging, code generation, and packet decoding.
"""

from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from embeddedcoder.inference.engine import EmbeddedCoder

app = FastAPI(
    title="EmbeddedCoder AI API",
    description="Universal Embedded Systems Engineering Small Language Model API",
    version="0.1.0"
)

# Lazy singleton engine
_engine: Optional[EmbeddedCoder] = None


def get_engine() -> EmbeddedCoder:
    global _engine
    if _engine is None:
        _engine = EmbeddedCoder(
            model_path="models/sft_checkpoint",
            base_model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
            offline=True
        )
    return _engine


# Request / Response Schemas
class DebugRequest(BaseModel):
    platform: str = Field(default="generic_cortex_m", description="Target platform: stm32, esp32, generic_embedded_linux, etc.")
    language: str = Field(default="c", description="c or cpp")
    logs: Optional[str] = Field(None, description="Crash dump, compiler errors, or serial logs")
    code: Optional[str] = Field(None, description="Faulty firmware source code")


class CodeGenRequest(BaseModel):
    prompt: str = Field(..., description="Engineering code generation task")
    platform: str = Field(default="generic_cortex_m")
    language: str = Field(default="c")


class PacketDecodeRequest(BaseModel):
    protocol: str = Field(..., description="modbus, can, j1939, obd2, or ais140")
    hex_bytes: str = Field(..., description="Hexadecimal raw byte string")


class LogExplainRequest(BaseModel):
    logs: str = Field(..., description="Raw UART logs, kernel dmesg, or HardFault register dump")
    architecture: str = Field(default="arm_cortex_m")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "EmbeddedCoder AI",
        "version": "0.1.0",
        "offline": True
    }


@app.get("/v1/model-info")
def model_info():
    return {
        "model_name": "EmbeddedCoder-1.5B",
        "base_model": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "parameters": "1.54B",
        "license": "Apache-2.0",
        "context_window": 32768,
        "capabilities": [
            "Embedded C/C++ generation",
            "Peripheral driver design (UART, SPI, I2C, CAN)",
            "RTOS concurrency triage",
            "Binary packet decoding (Modbus, CAN, AIS-140)",
            "Hardware diagnostic triage (HardFaults, Bus Errors)"
        ]
    }


@app.post("/v1/debug")
def debug_firmware(req: DebugRequest):
    try:
        engine = get_engine()
        result = engine.debug(
            platform=req.platform,
            language=req.language,
            logs=req.logs,
            code=req.code
        )
        return {
            "status": "success",
            "platform": req.platform,
            "diagnosis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/generate-code")
def generate_code(req: CodeGenRequest):
    try:
        engine = get_engine()
        result = engine.generate_code(
            prompt=req.prompt,
            platform=req.platform,
            language=req.language
        )
        return {
            "status": "success",
            "platform": req.platform,
            "language": req.language,
            "code": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/decode-packet")
def decode_packet(req: PacketDecodeRequest):
    try:
        engine = get_engine()
        result = engine.decode_packet(
            protocol=req.protocol,
            hex_bytes=req.hex_bytes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/explain-log")
def explain_log(req: LogExplainRequest):
    try:
        engine = get_engine()
        query = f"Architecture: {req.architecture}\nDiagnose and explain these logs:\n{req.logs}"
        explanation = engine.ask(query)
        return {
            "architecture": req.architecture,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
