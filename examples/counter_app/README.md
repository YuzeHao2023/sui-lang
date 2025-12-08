# Counter App Example

A simple counter application demonstrating Sui + WebAssembly + HTML/JS integration.

## Files

- `logic.sui` - Sui logic (counter state and operations)
- `index.html` - UI (vanilla JS)
- `logic.wasm` - Compiled WebAssembly (generated)

## Build & Run

```bash
# Compile Sui to WebAssembly
sui2wasm logic.sui -o logic.wasm

# Start local server
python -m http.server 8080

# Open in browser
open http://localhost:8080
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   index.html    │────▶│   logic.wasm    │
│   (UI Layer)    │     │   (Sui Logic)   │
└─────────────────┘     └─────────────────┘
        │                       │
        │   f0() increment      │
        │   f1() decrement      │
        │   f2() reset          │
        │   g0   state          │
        └───────────────────────┘
```

## Sui Exports

| Export | Type | Description |
|--------|------|-------------|
| `g0` | Global | Counter state (read via `.value`) |
| `f0()` | Function | Increment counter |
| `f1()` | Function | Decrement counter |
| `f2()` | Function | Reset to 0 |
| `main()` | Function | Initialize |

