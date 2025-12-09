# Sui Strategic Roadmap

> Goal: Make Sui the de facto standard for LLM code generation

## Current Status

| Area | Status | Evaluation |
|------|--------|------------|
| Language Design | High completeness | ✅ |
| Runtime | Python + Wasm | ✅ |
| Documentation | Basic only | ⚠️ |
| Ecosystem | None | ❌ |
| LLM Integration | Prompts only | ⚠️ |
| Awareness | Near zero | ❌ |

## Strategic Actions

### Priority 1: Benchmark Paper (Academic Proof)

**Goal**: Scientifically prove "LLMs can write Sui with 100% accuracy"

- [ ] Create `sui-bench` benchmark suite
- [ ] Compare Sui vs Python vs JavaScript
- [ ] Measure: syntax error rate, execution success rate, token efficiency
- [ ] Target venues: NeurIPS, ICML, ACL workshops
- [ ] Expected metrics:

| Metric | Sui | Python | JS |
|--------|-----|--------|-----|
| Syntax Error Rate | 0% | ~12% | ~15% |
| Execution Success | 100% | ~78% | ~72% |

### Priority 2: VSCode Extension (Developer Experience)

**Goal**: Lower adoption barrier for developers

- [ ] Syntax highlighting
- [ ] Code snippets
- [ ] Error diagnostics
- [ ] LSP (Language Server Protocol) implementation
- [ ] Cursor AI prompt optimization

### Priority 3: LLM Provider Outreach

**Goal**: Get Sui into LLM training data / system prompts

| Provider | Action | Status |
|----------|--------|--------|
| Anthropic | Direct contact, propose collaboration | ⬜ |
| OpenAI | Create Custom GPT for Sui | ⬜ |
| Google | DeepMind outreach | ⬜ |
| Hugging Face | Publish Sui dataset | ⬜ |

### Priority 4: Killer Application

**Goal**: Prove practical utility

Candidates:
- [ ] AI Agent logic description standard
- [ ] Smart contract logic layer
- [ ] Educational programming language
- [ ] Scientific computing (with math extensions)

### Priority 5: Standard Packages (#8, #9)

**Goal**: Provide common functionality via packages (not built-in)

- [ ] Package manager implementation (#9)
- [ ] `sui-math` package: matrix, statistics (#8)
- [ ] `sui-crypto` package: hash, encryption
- [ ] `sui-algo` package: sort, search, graph

See [Issue #8](https://github.com/TakatoHonda/sui-lang/issues/8) and [Issue #9](https://github.com/TakatoHonda/sui-lang/issues/9)

## Ecosystem Development

### Package Manager (#9)

**Design**: Hash-based package IDs (zero identifiers)

```
Package ID = hash(package_name)[:32bit]  → ~4 billion unique IDs
Function ID = sequential within package  → 65,536 per package
```

**Example:**
```sui
; X <pkg_id> <func_id> <result> <args...>
X 1829473628 0 v2 v0 v1   ; sui-math:matmul
X 562847193 0 v3 v0       ; sui-crypto:sha256
```

**Key Features:**
- Deterministic: same name → same ID (globally)
- Distributed: no central authority for ID assignment
- Collision handling: registry + salt on conflict (~0.001% at 10k packages)

See [Issue #9](https://github.com/TakatoHonda/sui-lang/issues/9)

### Standard Library

| Module | Operations |
|--------|------------|
| Math | Matrix, vector, statistics |
| String | (TBD - may require identifiers) |
| Crypto | Hash, encrypt/decrypt |

## Marketing & Awareness

- [ ] Twitter/X presence
- [ ] Blog posts explaining philosophy
- [ ] Conference talks (PyCon, JSConf, etc.)
- [ ] YouTube tutorials
- [ ] Collaboration with AI influencers

## Timeline (Proposed)

| Quarter | Focus |
|---------|-------|
| Q1 2025 | Benchmark paper, VSCode extension |
| Q2 2025 | LLM provider outreach, killer app prototype |
| Q3 2025 | Math extensions, package ecosystem design |
| Q4 2025 | Community building, standardization efforts |

## Success Metrics

| Metric | Target (1 year) |
|--------|-----------------|
| GitHub Stars | 1,000+ |
| PyPI Downloads/month | 10,000+ |
| Academic Citations | 10+ |
| LLM native support | 1+ provider |

## Core Philosophy (Never Compromise)

1. **Zero syntax errors** - Structural guarantee
2. **Zero typos** - Variables are numbers only
3. **One instruction per line** - Line independence
4. **Pure logic** - UI/IO delegated to external frameworks
5. **No identifiers** - All operations use numeric IDs

---

*"Sui is the sanctuary of logic. The dirty outside world is left to existing languages."*

