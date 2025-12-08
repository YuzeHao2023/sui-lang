#!/usr/bin/env python3
"""
Sui to WebAssembly Binary Compiler

Compiles Sui code directly to Wasm binary (.wasm) file.
Uses sui2wat internally, then wat2wasm for binary conversion.
"""

import sys
import subprocess
import tempfile
import os

from sui2wat import Sui2WatTranspiler


def compile_to_wasm(sui_code: str) -> bytes | None:
    """Compile Sui code to Wasm binary"""
    # First, transpile to WAT
    transpiler = Sui2WatTranspiler()
    wat_code = transpiler.transpile(sui_code)
    
    # Then compile WAT to Wasm using wat2wasm
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.wat', delete=False) as f:
            f.write(wat_code)
            wat_path = f.name
        
        wasm_path = wat_path.replace('.wat', '.wasm')
        
        result = subprocess.run(
            ['wat2wasm', wat_path, '-o', wasm_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: wat2wasm failed: {result.stderr}", file=sys.stderr)
            return None
        
        with open(wasm_path, 'rb') as f:
            wasm_bytes = f.read()
        
        # Cleanup
        os.unlink(wat_path)
        os.unlink(wasm_path)
        
        return wasm_bytes
        
    except FileNotFoundError:
        print("Error: wat2wasm not found. Install wabt: brew install wabt", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("Usage: sui2wasm <input.sui> [-o <output.wasm>]")
        print()
        print("Compile Sui code to WebAssembly binary.")
        print()
        print("Options:")
        print("  -o FILE    Output file (default: input.wasm)")
        print()
        print("Requirements:")
        print("  wat2wasm   Install via: brew install wabt")
        sys.exit(0 if '-h' in sys.argv or '--help' in sys.argv else 1)
    
    input_file = sys.argv[1]
    
    # Determine output file
    output_file = input_file.rsplit('.', 1)[0] + '.wasm'
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    # Read input
    try:
        with open(input_file, 'r') as f:
            sui_code = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    # Compile
    wasm_bytes = compile_to_wasm(sui_code)
    
    if wasm_bytes is None:
        sys.exit(1)
    
    # Write output
    with open(output_file, 'wb') as f:
        f.write(wasm_bytes)
    
    print(f"✓ Compiled to {output_file} ({len(wasm_bytes)} bytes)")


if __name__ == '__main__':
    main()

