"""Tests for Sui to WAT transpiler (sui2wat)"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sui2wasm import Sui2WatTranspiler


class TestSui2WatBasic:
    """Test basic WAT transpilation"""

    def test_assignment(self):
        """Test variable assignment"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= g0 42")
        assert "(i32.const 42)" in code
        assert "(global.set $g0)" in code

    def test_local_assignment(self):
        """Test local variable assignment"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= v0 10")
        assert "(i32.const 10)" in code
        assert "(local.set $v0)" in code

    def test_arithmetic_add(self):
        """Test addition"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= v0 5\n= v1 3\n+ v2 v0 v1")
        assert "(i32.add)" in code
        assert "(local.set $v2)" in code

    def test_arithmetic_sub(self):
        """Test subtraction"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("- v0 10 3")
        assert "(i32.sub)" in code

    def test_arithmetic_mul(self):
        """Test multiplication"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("* v0 4 5")
        assert "(i32.mul)" in code

    def test_arithmetic_div(self):
        """Test division"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("/ v0 20 4")
        assert "(i32.div_s)" in code

    def test_arithmetic_mod(self):
        """Test modulo"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("% v0 17 5")
        assert "(i32.rem_s)" in code


class TestSui2WatComparisons:
    """Test comparison operations"""

    def test_less_than(self):
        """Test less than comparison"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("< v0 3 5")
        assert "(i32.lt_s)" in code

    def test_greater_than(self):
        """Test greater than comparison"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("> v0 5 3")
        assert "(i32.gt_s)" in code

    def test_equality(self):
        """Test equality comparison"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("~ v0 5 5")
        assert "(i32.eq)" in code


class TestSui2WatLogic:
    """Test logical operations"""

    def test_not(self):
        """Test NOT operation"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= v0 0\n! v1 v0")
        assert "(i32.eqz)" in code

    def test_and(self):
        """Test AND operation"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("& v0 1 1")
        assert "(i32.and)" in code

    def test_or(self):
        """Test OR operation"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("| v0 0 1")
        assert "(i32.or)" in code


class TestSui2WatOutput:
    """Test output operation"""

    def test_print(self):
        """Test print operation imports external function"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile(". 42")
        assert '(import "env" "print_i32"' in code
        assert "(call $print_i32)" in code


class TestSui2WatLabelsJumps:
    """Test labels and jumps (state machine pattern)"""

    def test_label_creates_state(self):
        """Test that labels create states"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile(": 0\n: 1")
        assert "(local $_state i32)" in code
        assert "(block $exit" in code
        assert "(loop $loop" in code

    def test_unconditional_jump(self):
        """Test unconditional jump"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile(": 0\n@ 0")
        assert "(local.set $_state" in code
        assert "(br $loop)" in code

    def test_conditional_jump(self):
        """Test conditional jump"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= v0 1\n: 0\n? v0 1\n: 1")
        assert "(if" in code
        assert "(br $loop)" in code

    def test_loop_pattern(self):
        """Test a typical loop pattern"""
        sui_code = """
= v0 0
: 0
< v1 v0 10
! v2 v1
? v2 1
+ v0 v0 1
@ 0
: 1
"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile(sui_code)
        # Should have state machine structure
        assert "State 0" in code or "_state" in code
        assert "(loop $loop" in code


class TestSui2WatArrays:
    """Test array operations"""

    def test_array_creates_memory(self):
        """Test that array operations create memory"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("[ g0 5")
        assert "(memory 1)" in code
        assert "(global $heap_ptr" in code

    def test_array_create(self):
        """Test array creation"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("[ g0 10")
        assert "(global.get $heap_ptr)" in code
        assert "(global.set $heap_ptr)" in code

    def test_array_write(self):
        """Test array write"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("[ g0 5\n{ g0 0 42")
        assert "(i32.store)" in code

    def test_array_read(self):
        """Test array read"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("[ g0 5\n{ g0 0 42\n] v0 g0 0")
        assert "(i32.load)" in code


class TestSui2WatFunctions:
    """Test function definitions and calls"""

    def test_function_definition(self):
        """Test function definition"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("# 0 1 {\n^ a0\n}")
        assert "(func $f0" in code
        assert "(param $a0 i32)" in code
        assert "(result i32)" in code

    def test_function_with_multiple_params(self):
        """Test function with multiple parameters"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("# 0 3 {\n+ v0 a0 a1\n+ v1 v0 a2\n^ v1\n}")
        assert "(param $a0 i32)" in code
        assert "(param $a1 i32)" in code
        assert "(param $a2 i32)" in code

    def test_function_call(self):
        """Test function call"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("# 0 1 {\n^ a0\n}\n$ g0 0 42")
        assert "(call $f0)" in code

    def test_return_statement(self):
        """Test return statement"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("# 0 1 {\n^ a0\n}")
        assert "(return)" in code


class TestSui2WatModuleStructure:
    """Test overall module structure"""

    def test_module_wrapper(self):
        """Test that output is wrapped in module"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= g0 1")
        assert code.startswith("(module")
        assert code.strip().endswith(")")

    def test_main_function_export(self):
        """Test that main function is exported"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= g0 1")
        assert '(func $main (export "main")' in code

    def test_main_returns_i32(self):
        """Test that main returns i32"""
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile("= g0 1")
        assert "(result i32)" in code


class TestSui2WatExamples:
    """Test that example files transpile without errors"""

    @pytest.fixture
    def examples_dir(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')

    def test_fibonacci_transpiles(self, examples_dir):
        """Test fibonacci.sui transpiles"""
        with open(os.path.join(examples_dir, 'fibonacci.sui')) as f:
            sui_code = f.read()
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile(sui_code)
        assert "(module" in code
        assert "(func $f0" in code  # Fibonacci function

    def test_fizzbuzz_transpiles(self, examples_dir):
        """Test fizzbuzz.sui transpiles"""
        with open(os.path.join(examples_dir, 'fizzbuzz.sui')) as f:
            sui_code = f.read()
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile(sui_code)
        assert "(module" in code
        assert "(loop $loop" in code  # Should have loop structure

    def test_list_sum_transpiles(self, examples_dir):
        """Test list_sum.sui transpiles with memory"""
        with open(os.path.join(examples_dir, 'list_sum.sui')) as f:
            sui_code = f.read()
        transpiler = Sui2WatTranspiler()
        code = transpiler.transpile(sui_code)
        assert "(module" in code
        assert "(memory 1)" in code  # Should have memory for arrays
        assert "(i32.store)" in code  # Array writes
        assert "(i32.load)" in code   # Array reads

