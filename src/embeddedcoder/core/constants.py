"""
Core constants, domain taxonomies, and hardware architecture definitions for EmbeddedCoder AI.
"""

from enum import Enum
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EVAL_DATA_DIR = DATA_DIR / "evaluation"
MANIFESTS_DIR = DATA_DIR / "manifests"
CONFIGS_DIR = PROJECT_ROOT / "configs"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
TOOLS_DIR = PROJECT_ROOT / "tools"

# Explicitly ensure Hugging Face caches default to D: drive
HF_CACHE_DIR = PROJECT_ROOT / ".cache" / "huggingface"
os.environ.setdefault("HF_HOME", str(HF_CACHE_DIR))

# Portable toolchain paths
GCC_PATH = TOOLS_DIR / "w64devkit" / "bin" / "gcc.exe"
GPP_PATH = TOOLS_DIR / "w64devkit" / "bin" / "g++.exe"


class Subdomain(str, Enum):
    EMBEDDED_C_CPP = "embedded_c_cpp"
    MCUS_SOCS = "mcus_socs"
    PERIPHERALS_DRIVERS = "peripherals_drivers"
    RTOS_CONCURRENCY = "rtos_concurrency"
    EMBEDDED_LINUX = "embedded_linux"
    PROTOCOLS_TELEMETRY = "protocols_telemetry"
    WIRELESS_IOT = "wireless_iot"
    HARDWARE_DIAGNOSTICS = "hardware_diagnostics"
    POWER_SECURITY = "power_security"


class Architecture(str, Enum):
    ARM_CORTEX_M = "arm_cortex_m"
    ARM_CORTEX_A = "arm_cortex_a"
    RISCV = "riscv"
    XTENSA = "xtensa"
    AVR = "avr"
    GENERIC = "generic"


class HardwarePlatform(str, Enum):
    STM32 = "stm32"
    ESP32 = "esp32"
    RP2040 = "rp2040"
    NXP_IMX = "nxp_imx"
    TI_MSP = "ti_msp"
    AVR_MEGA = "avr_mega"
    GENERIC_CORTEX_M = "generic_cortex_m"
    EMBEDDED_LINUX = "generic_embedded_linux"
    QUECTEL_CELLULAR = "quectel_cellular"
    SIMCOM_CELLULAR = "simcom_cellular"
    UNIVERSAL = "universal"


class VerificationMethod(str, Enum):
    GCC_COMPILATION = "gcc_compilation"
    UNIT_TEST = "unit_test"
    CRC_VERIFICATION = "crc_verification"
    GOLDEN_PACKET_DECODE = "golden_packet_decode"
    DIAGNOSTIC_TRIAGE = "diagnostic_triage"
    CITATION_CHECK = "citation_check"
    HONEST_UNCERTAINTY = "honest_uncertainty"
