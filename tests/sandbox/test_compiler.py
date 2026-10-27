"""
Unit tests for the C/C++ compilation and execution sandbox.
"""

import pytest
from embeddedcoder.sandbox.compiler import SandboxCompiler


@pytest.fixture
def compiler():
    return SandboxCompiler()


def test_successful_c_compilation(compiler):
    c_code = """
    #include <stdio.h>
    #include <stdint.h>

    int main(void) {
        uint32_t val = 0xAABBCCDD;
        printf("HEX: 0x%08X\\n", (unsigned int)val);
        return 0;
    }
    """
    res = compiler.compile_and_run(c_code, is_cpp=False)
    assert res.success is True
    assert res.exit_code == 0
    assert "HEX: 0xAABBCCDD" in res.execution_stdout


def test_warning_as_error_rejection(compiler):
    # Unused variable should trigger -Wunused-variable and fail compilation under -Werror
    bad_code = """
    #include <stdio.h>

    int main(void) {
        int unused_var = 42;
        printf("Hello\\n");
        return 0;
    }
    """
    res = compiler.compile_and_run(bad_code, is_cpp=False)
    assert res.success is False
    assert res.exit_code != 0
    assert "unused-variable" in res.stderr.lower() or "error" in res.stderr.lower()


def test_cpp_compilation(compiler):
    cpp_code = """
    #include <iostream>
    #include <array>

    int main() {
        std::array<int, 3> arr = {1, 2, 3};
        int sum = 0;
        for (const auto& item : arr) {
            sum += item;
        }
        std::cout << "SUM=" << sum << std::endl;
        return 0;
    }
    """
    res = compiler.compile_and_run(cpp_code, is_cpp=True)
    assert res.success is True
    assert "SUM=6" in res.execution_stdout
