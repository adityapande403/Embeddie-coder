"""
Deterministic compilation and sandboxed execution engine for generated C and C++ code.
Uses the verified local GCC toolchain with strict warning enforcement and timeouts.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional
from embeddedcoder.core.constants import GCC_PATH, GPP_PATH


class CompilationResult:
    def __init__(
        self,
        success: bool,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
        execution_stdout: str = "",
        execution_stderr: str = "",
        execution_exit_code: Optional[int] = None,
        duration_ms: float = 0.0,
    ):
        self.success = success
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_stdout = execution_stdout
        self.execution_stderr = execution_stderr
        self.execution_exit_code = execution_exit_code
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_stdout": self.execution_stdout,
            "execution_stderr": self.execution_stderr,
            "execution_exit_code": self.execution_exit_code,
            "duration_ms": self.duration_ms,
        }


class SandboxCompiler:
    def __init__(self, gcc_path: Optional[Path] = None, gpp_path: Optional[Path] = None):
        self.gcc_path = gcc_path or GCC_PATH
        self.gpp_path = gpp_path or GPP_PATH

        if not self.gcc_path.exists():
            raise FileNotFoundError(f"GCC compiler not found at {self.gcc_path}")

    def compile_and_run(
        self,
        code: str,
        is_cpp: bool = False,
        compile_timeout_s: float = 5.0,
        run_timeout_s: float = 3.0,
        extra_flags: Optional[list] = None,
        run_binary: bool = True,
    ) -> CompilationResult:
        """
        Safely compile and run C/C++ code in a temporary directory.
        Strict warnings enabled: -Wall -Wextra -Werror.
        """
        start_time = time.perf_counter()
        compiler = str(self.gpp_path if is_cpp else self.gcc_path)
        std_flag = "-std=c++17" if is_cpp else "-std=c11"
        ext = ".cpp" if is_cpp else ".c"

        flags = [
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            std_flag,
        ]
        if extra_flags:
            flags.extend(extra_flags)

        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = Path(tmpdir) / f"source{ext}"
            bin_file = Path(tmpdir) / "output.exe"

            # Write source code
            src_file.write_text(code, encoding="utf-8")

            # Compile step
            cmd = [compiler] + flags + [str(src_file), "-o", str(bin_file)]
            try:
                comp_proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=compile_timeout_s,
                    cwd=tmpdir,
                )
            except subprocess.TimeoutExpired:
                duration = (time.perf_counter() - start_time) * 1000.0
                return CompilationResult(
                    success=False,
                    exit_code=-1,
                    stderr="Compilation timed out.",
                    duration_ms=duration,
                )

            if comp_proc.returncode != 0:
                duration = (time.perf_counter() - start_time) * 1000.0
                return CompilationResult(
                    success=False,
                    exit_code=comp_proc.returncode,
                    stdout=comp_proc.stdout,
                    stderr=comp_proc.stderr,
                    duration_ms=duration,
                )

            # Execution step
            exec_stdout = ""
            exec_stderr = ""
            exec_returncode = 0

            if run_binary and bin_file.exists():
                try:
                    run_proc = subprocess.run(
                        [str(bin_file)],
                        capture_output=True,
                        text=True,
                        timeout=run_timeout_s,
                        cwd=tmpdir,
                    )
                    exec_stdout = run_proc.stdout
                    exec_stderr = run_proc.stderr
                    exec_returncode = run_proc.returncode
                except subprocess.TimeoutExpired:
                    duration = (time.perf_counter() - start_time) * 1000.0
                    return CompilationResult(
                        success=False,
                        exit_code=0,
                        stdout=comp_proc.stdout,
                        execution_stderr="Execution timed out.",
                        execution_exit_code=-2,
                        duration_ms=duration,
                    )

            duration = (time.perf_counter() - start_time) * 1000.0
            is_successful = (comp_proc.returncode == 0) and (exec_returncode == 0)

            return CompilationResult(
                success=is_successful,
                exit_code=comp_proc.returncode,
                stdout=comp_proc.stdout,
                stderr=comp_proc.stderr,
                execution_stdout=exec_stdout,
                execution_stderr=exec_stderr,
                execution_exit_code=exec_returncode,
                duration_ms=duration,
            )
