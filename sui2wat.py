#!/usr/bin/env python3
"""
Sui (粋) to WebAssembly Text Format (WAT) Transpiler
Convert Sui code to WAT for WebAssembly execution
"""

import sys
from typing import Optional


class Sui2WatTranspiler:
    """Sui to WAT transpiler"""

    def __init__(self):
        self.output: list[str] = []
        self.indent = 0
        self.functions: dict[int, dict] = {}
        self.global_count = 0
        self.local_count = 0
        self.label_count = 0
        # Track used variables
        self.used_globals: set[int] = set()
        self.used_locals: set[int] = set()

    def emit(self, line: str):
        """Emit a line with proper indentation"""
        self.output.append("  " * self.indent + line)

    def parse_line(self, line: str) -> list[str] | None:
        """Parse a single line"""
        if ';' in line:
            line = line[:line.index(';')]
        line = line.strip()
        if not line:
            return None
        
        tokens = []
        i = 0
        while i < len(line):
            if line[i] in ' \t':
                i += 1
                continue
            if line[i] == '"':
                j = i + 1
                while j < len(line) and line[j] != '"':
                    if line[j] == '\\':
                        j += 2
                    else:
                        j += 1
                tokens.append(line[i:j + 1])
                i = j + 1
                continue
            j = i
            while j < len(line) and line[j] not in ' \t':
                j += 1
            tokens.append(line[i:j])
            i = j
        return tokens if tokens else None

    def collect_variables(self, lines: list[list[str]]):
        """Collect used variables"""
        for tokens in lines:
            if not tokens:
                continue
            for token in tokens[1:]:
                if token.startswith('v'):
                    try:
                        self.used_locals.add(int(token[1:]))
                    except ValueError:
                        pass
                elif token.startswith('g'):
                    try:
                        self.used_globals.add(int(token[1:]))
                    except ValueError:
                        pass

    def resolve_value(self, val: str) -> tuple[str, str]:
        """
        Resolve a value to WAT code
        Returns: (WAT instruction, type)
        """
        if val.startswith('v'):
            idx = int(val[1:])
            return f"(local.get $v{idx})", "i32"
        elif val.startswith('g'):
            idx = int(val[1:])
            return f"(global.get $g{idx})", "i32"
        elif val.startswith('a'):
            idx = int(val[1:])
            return f"(local.get $a{idx})", "i32"
        elif val.startswith('"'):
            # Strings not yet supported (requires memory operations)
            return "(i32.const 0)", "i32"
        elif '.' in val:
            return f"(f64.const {val})", "f64"
        else:
            try:
                return f"(i32.const {int(val)})", "i32"
            except ValueError:
                return "(i32.const 0)", "i32"

    def assign_value(self, var: str, value_code: str) -> str:
        """Generate WAT instruction for variable assignment"""
        if var.startswith('v'):
            idx = int(var[1:])
            return f"{value_code}\n    (local.set $v{idx})"
        elif var.startswith('g'):
            idx = int(var[1:])
            return f"{value_code}\n    (global.set $g{idx})"
        return ""

    def transpile_instruction(self, tokens: list[str]) -> list[str]:
        """Transpile a single instruction to WAT"""
        if not tokens:
            return []
        
        op = tokens[0]
        result = []

        if op == '=':
            # Assignment: = var val
            val_code, _ = self.resolve_value(tokens[2])
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"{val_code}")
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"{val_code}")
                result.append(f"(global.set $g{idx})")

        elif op in ['+', '-', '*', '/', '%']:
            # Arithmetic: op result a b
            a_code, _ = self.resolve_value(tokens[2])
            b_code, _ = self.resolve_value(tokens[3])
            
            op_map = {
                '+': 'i32.add',
                '-': 'i32.sub',
                '*': 'i32.mul',
                '/': 'i32.div_s',
                '%': 'i32.rem_s'
            }
            
            result.append(f"{a_code}")
            result.append(f"{b_code}")
            result.append(f"({op_map[op]})")
            
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"(global.set $g{idx})")

        elif op == '<':
            # Less than: < result a b
            a_code, _ = self.resolve_value(tokens[2])
            b_code, _ = self.resolve_value(tokens[3])
            result.append(f"{a_code}")
            result.append(f"{b_code}")
            result.append("(i32.lt_s)")
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"(global.set $g{idx})")

        elif op == '>':
            # Greater than: > result a b
            a_code, _ = self.resolve_value(tokens[2])
            b_code, _ = self.resolve_value(tokens[3])
            result.append(f"{a_code}")
            result.append(f"{b_code}")
            result.append("(i32.gt_s)")
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"(global.set $g{idx})")

        elif op == '~':
            # Equality: ~ result a b
            a_code, _ = self.resolve_value(tokens[2])
            b_code, _ = self.resolve_value(tokens[3])
            result.append(f"{a_code}")
            result.append(f"{b_code}")
            result.append("(i32.eq)")
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"(global.set $g{idx})")

        elif op == '!':
            # NOT: ! result a
            a_code, _ = self.resolve_value(tokens[2])
            result.append(f"{a_code}")
            result.append("(i32.eqz)")
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"(global.set $g{idx})")

        elif op == '&':
            # AND: & result a b
            a_code, _ = self.resolve_value(tokens[2])
            b_code, _ = self.resolve_value(tokens[3])
            result.append(f"{a_code}")
            result.append(f"{b_code}")
            result.append("(i32.and)")
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"(global.set $g{idx})")

        elif op == '|':
            # OR: | result a b
            a_code, _ = self.resolve_value(tokens[2])
            b_code, _ = self.resolve_value(tokens[3])
            result.append(f"{a_code}")
            result.append(f"{b_code}")
            result.append("(i32.or)")
            if tokens[1].startswith('v'):
                idx = int(tokens[1][1:])
                result.append(f"(local.set $v{idx})")
            elif tokens[1].startswith('g'):
                idx = int(tokens[1][1:])
                result.append(f"(global.set $g{idx})")

        elif op == '^':
            # Return: ^ value
            val_code, _ = self.resolve_value(tokens[1])
            result.append(f"{val_code}")
            result.append("(return)")

        elif op == '.':
            # Output: . value (external function call)
            val_code, _ = self.resolve_value(tokens[1])
            result.append(f"{val_code}")
            result.append("(call $print_i32)")

        return result

    def transpile_function(self, func_id: int, argc: int, body: list[list[str]]) -> list[str]:
        """Transpile a function to WAT"""
        result = []
        
        # Collect local variables used in function
        local_vars: set[int] = set()
        for tokens in body:
            if not tokens:
                continue
            for token in tokens:
                if token.startswith('v'):
                    try:
                        local_vars.add(int(token[1:]))
                    except ValueError:
                        pass

        # Function signature
        params = " ".join(f"(param $a{i} i32)" for i in range(argc))
        result.append(f"(func $f{func_id} {params} (result i32)")
        
        # Local variable declarations
        for v in sorted(local_vars):
            result.append(f"  (local $v{v} i32)")
        
        # Function body
        for tokens in body:
            if tokens and tokens[0] != '}':
                instructions = self.transpile_instruction(tokens)
                for inst in instructions:
                    result.append(f"  {inst}")
        
        # Default return value
        result.append("  (i32.const 0)")
        result.append(")")
        
        return result

    def transpile(self, code: str) -> str:
        """Transpile Sui code to WAT"""
        self.output = []
        self.used_globals = set()
        self.used_locals = set()
        
        lines_raw = code.strip().split('\n')
        lines = []
        for line in lines_raw:
            parsed = self.parse_line(line)
            if parsed:
                lines.append(parsed)

        # Collect variables
        self.collect_variables(lines)

        # Collect functions
        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
                func_id = int(lines[i][1])
                argc = int(lines[i][2])
                body = []
                i += 1
                depth = 1
                while i < len(lines) and depth > 0:
                    if lines[i][0] == '#':
                        depth += 1
                    elif lines[i][0] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    body.append(lines[i])
                    i += 1
                self.functions[func_id] = {'argc': argc, 'body': body}
            i += 1

        # WAT output start
        self.emit("(module")
        self.indent += 1

        # Import (print function)
        self.emit(";; External function imports")
        self.emit('(import "env" "print_i32" (func $print_i32 (param i32)))')
        self.emit("")

        # Global variables
        if self.used_globals:
            self.emit(";; Global variables")
            for g in sorted(self.used_globals):
                self.emit(f"(global $g{g} (mut i32) (i32.const 0))")
            self.emit("")

        # Function definitions
        if self.functions:
            self.emit(";; Function definitions")
            for func_id, func_info in sorted(self.functions.items()):
                func_lines = self.transpile_function(
                    func_id, 
                    func_info['argc'], 
                    func_info['body']
                )
                for line in func_lines:
                    self.emit(line)
                self.emit("")

        # Main function
        self.emit(";; Main function")
        self.emit("(func $main (export \"main\") (result i32)")
        self.indent += 1

        # Local variables used in main
        main_locals: set[int] = set()
        main_lines = []
        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
                depth = 1
                i += 1
                while i < len(lines) and depth > 0:
                    if lines[i][0] == '#':
                        depth += 1
                    elif lines[i][0] == '}':
                        depth -= 1
                    i += 1
            else:
                main_lines.append(lines[i])
                for token in lines[i]:
                    if token.startswith('v'):
                        try:
                            main_locals.add(int(token[1:]))
                        except ValueError:
                            pass
                i += 1

        # Local variable declarations
        for v in sorted(main_locals):
            self.emit(f"(local $v{v} i32)")

        # Main body
        for tokens in main_lines:
            if tokens[0] == '$':
                # Function call: $ result func_id args...
                result_var = tokens[1]
                func_id = tokens[2]
                args = tokens[3:]
                
                for arg in args:
                    val_code, _ = self.resolve_value(arg)
                    self.emit(val_code)
                self.emit(f"(call $f{func_id})")
                
                if result_var.startswith('v'):
                    idx = int(result_var[1:])
                    self.emit(f"(local.set $v{idx})")
                elif result_var.startswith('g'):
                    idx = int(result_var[1:])
                    self.emit(f"(global.set $g{idx})")
            else:
                instructions = self.transpile_instruction(tokens)
                for inst in instructions:
                    self.emit(inst)

        # Return value
        self.emit("(i32.const 0)")
        self.indent -= 1
        self.emit(")")

        self.indent -= 1
        self.emit(")")

        return '\n'.join(self.output)


def main():
    if len(sys.argv) < 2:
        print("Sui (粋) to WebAssembly Text Format Transpiler")
        print("=" * 50)
        print("")
        print("Usage:")
        print("  sui2wat <file.sui>            # Output WAT to stdout")
        print("  sui2wat <file.sui> -o out.wat # Output to file")
        print("")
        print("Then convert to binary with wat2wasm:")
        print("  wat2wasm out.wat -o out.wasm")
        print("")
        print("Sample:")
        print("-" * 50)

        sample = """
= g0 10
+ g1 g0 5
. g1
"""
        print("Sui:")
        print(sample.strip())
        print("")
        print("WAT:")
        transpiler = Sui2WatTranspiler()
        result = transpiler.transpile(sample)
        print(result)
        return

    filename = sys.argv[1]

    with open(filename, 'r') as f:
        code = f.read()

    transpiler = Sui2WatTranspiler()
    wat_code = transpiler.transpile(code)

    if '-o' in sys.argv:
        out_idx = sys.argv.index('-o')
        out_file = sys.argv[out_idx + 1]
        with open(out_file, 'w') as f:
            f.write(wat_code)
        print(f"✓ Output saved to {out_file}")
    else:
        print(wat_code)


if __name__ == '__main__':
    main()

