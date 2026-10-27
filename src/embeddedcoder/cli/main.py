"""
Command-line interface (CLI) for EmbeddedCoder AI.
Enables command-line firmware debugging, code generation, and packet decoding.
"""

import click
import json
from embeddedcoder.inference.engine import EmbeddedCoder
from embeddedcoder import __version__


@click.group()
@click.version_option(version=__version__, prog_name="EmbeddedCoder AI")
def cli():
    """EmbeddedCoder AI — Universal Embedded Systems Engineering Assistant."""
    pass


@cli.command()
@click.argument("prompt")
@click.option("--model-path", default="models/sft_checkpoint", help="Path to checkpoint or merged model")
@click.option("--max-tokens", default=512, help="Maximum generated tokens")
def ask(prompt: str, model_path: str, max_tokens: int):
    """Ask an embedded systems engineering question."""
    click.echo(f"[*] Initializing EmbeddedCoder from {model_path}...")
    assistant = EmbeddedCoder(model_path=model_path, offline=True)
    click.echo("[*] Generating response...\n")
    response = assistant.ask(prompt, max_new_tokens=max_tokens)
    click.echo(response)


@cli.command()
@click.option("--prompt", required=True, help="Driver or firmware requirement")
@click.option("--platform", default="generic_cortex_m", help="Target hardware platform")
@click.option("--language", default="c", help="c or cpp")
@click.option("--model-path", default="models/sft_checkpoint", help="Path to checkpoint")
def generate_code(prompt: str, platform: str, language: str, model_path: str):
    """Generate production-quality embedded firmware or peripheral driver code."""
    click.echo(f"[*] Generating {language.upper()} code for platform: {platform}...")
    assistant = EmbeddedCoder(model_path=model_path, offline=True)
    code = assistant.generate_code(prompt=prompt, platform=platform, language=language)
    click.echo("\n" + code)


@cli.command()
@click.option("--logs", required=True, help="Serial logs, bus error registers, or crash dump")
@click.option("--platform", default="generic_cortex_m", help="Target hardware platform")
@click.option("--code", default=None, help="Optional source code snippet around crash")
@click.option("--model-path", default="models/sft_checkpoint", help="Path to checkpoint")
def debug(logs: str, platform: str, code: str, model_path: str):
    """Diagnose firmware crashes, HardFaults, or bus errors."""
    click.echo(f"[*] Analyzing diagnostic symptoms for platform: {platform}...")
    assistant = EmbeddedCoder(model_path=model_path, offline=True)
    diagnosis = assistant.debug(platform=platform, logs=logs, code=code)
    click.echo("\n" + diagnosis)


@cli.command()
@click.option("--protocol", required=True, help="modbus, can, j1939, obd2, or ais140")
@click.option("--hex-bytes", required=True, help="Raw frame in hexadecimal")
@click.option("--model-path", default="models/sft_checkpoint", help="Path to checkpoint")
def decode_packet(protocol: str, hex_bytes: str, model_path: str):
    """Decode and explain binary telemetry packets."""
    click.echo(f"[*] Decoding {protocol.upper()} frame: {hex_bytes}...")
    assistant = EmbeddedCoder(model_path=model_path, offline=True)
    result = assistant.decode_packet(protocol=protocol, hex_bytes=hex_bytes)
    click.echo("\nDeterministic Fields:")
    click.echo(json.dumps(result["deterministic_fields"], indent=2))
    click.echo("\nAI Protocol Explanation:")
    click.echo(result["ai_explanation"])


@cli.command()
def info():
    """Display EmbeddedCoder AI system information and capabilities."""
    click.echo(f"EmbeddedCoder AI v{__version__}")
    click.echo("Specialized Universal Embedded Systems Engineering SLM")
    click.echo("License: Apache-2.0")
    click.echo("Supported Architectures: ARM Cortex-M/A, RISC-V, ESP32, STM32, RP2040, AVR, Linux")
    click.echo("Deterministic Protocols: Modbus RTU/TCP, CAN 2.0B / J1939, OBD-II, AIS-140")


if __name__ == "__main__":
    cli()
