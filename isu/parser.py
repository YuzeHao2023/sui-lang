"""
Parse Isu text into IIR (AST).

v0 supports only a minimal subset:
- Sections: META/FUNC/IO/STATE/LOCAL/STEPS
- Root: STEPS must start with `SEQ: BEGIN` and end with `END`
- Nodes: ASSIGN / IF / LOOP / RETURN
- Expressions: S-expressions (e.g., (add ...), (call ...), ...)
"""

from __future__ import annotations

import re
from typing import Any, Optional

from isu.canonicalize import canonicalize
from isu.ir import Expr, Program, Stmt
from isu.sexpr import parse_expr


_STEP_ID_RE = re.compile(r"^S\d+(?:_\d+)*$")
_TOP_SECTIONS = {"META", "FUNC", "IO", "STATE", "LOCAL", "STEPS"}


class IsuParseError(ValueError):
    """Isu syntax error."""


def parse_isu(text: str, *, do_canonicalize: bool = True) -> Program:
    """Parse Isu text into a Program."""
    lines = _preprocess_lines(text)
    sections = _split_sections(lines)

    meta = _parse_mapping_section(sections.get("META", []))
    func = _parse_mapping_section(sections.get("FUNC", []))
    io = _parse_mapping_section(sections.get("IO", []))
    state = _parse_list_section(sections.get("STATE", []))
    local = _parse_list_section(sections.get("LOCAL", []))
    steps_lines = sections.get("STEPS", [])
    steps = _parse_steps(steps_lines)

    program = Program(meta=meta, func=func, io=io, state=state, local=local, steps=steps)
    return canonicalize(program) if do_canonicalize else program


def _preprocess_lines(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith(";"):
            continue
        out.append(line)
    return out


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: Optional[str] = None
    for line in lines:
        stripped = line.strip()
        # Section headers must be at column 0 (no indentation).
        if (line[:1] not in (" ", "\t")) and stripped.endswith(":") and stripped[:-1] in _TOP_SECTIONS:
            current = stripped[:-1]
            sections.setdefault(current, [])
            continue
        if current is None:
            raise IsuParseError("Found content before any section header")
        sections[current].append(stripped)
    return sections


def _parse_mapping_section(lines: list[str]) -> dict[str, Any]:
    m: dict[str, Any] = {}
    for line in lines:
        if ":" not in line:
            raise IsuParseError(f"Invalid mapping entry: {line}")
        k, v = [p.strip() for p in line.split(":", 1)]
        if not k:
            raise IsuParseError("Empty key")
        m[k] = _parse_scalar(v)
    return m


def _parse_list_section(lines: list[str]) -> list[Any]:
    if not lines:
        return []
    # Shorthand like `STATE: []`
    if len(lines) == 1 and lines[0] == "[]":
        return []
    out: list[Any] = []
    for line in lines:
        if line.startswith("- "):
            out.append(_parse_scalar(line[2:].strip()))
        else:
            # For compatibility, allow one scalar per line.
            out.append(_parse_scalar(line))
    return out


def _parse_scalar(s: str) -> Any:
    if s == "[]":
        return []
    if s == "true":
        return True
    if s == "false":
        return False
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        return s[1:-1]
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _parse_steps(lines: list[str]) -> Stmt:
    if not lines:
        raise IsuParseError("STEPS is empty")
    # v0: require `SEQ: BEGIN`
    head = lines[0]
    if head.upper() != "SEQ: BEGIN":
        raise IsuParseError("In v0, STEPS must start with 'SEQ: BEGIN'")
    if lines[-1].upper() != "END":
        raise IsuParseError("In v0, STEPS must end with 'END'")

    body_lines = lines[1:-1]
    stmts, idx = _parse_stmt_list(body_lines, 0, until_end=False)
    if idx != len(body_lines):
        raise IsuParseError("Unexpected trailing tokens in STEPS")
    return Stmt(kind="seq", step_id=None, data={"stmts": stmts})


def _parse_stmt_list(lines: list[str], start: int, *, until_end: bool) -> tuple[list[Stmt], int]:
    stmts: list[Stmt] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if until_end and line.upper() == "END":
            return stmts, i + 1
        if line.upper() == "END":
            raise IsuParseError("END without a matching BEGIN")
        stmt, i = _parse_stmt(lines, i)
        stmts.append(stmt)
    if until_end:
        raise IsuParseError("BEGIN without a matching END")
    return stmts, i


def _parse_stmt(lines: list[str], i: int) -> tuple[Stmt, int]:
    step_id, node, _label = _parse_stmt_head(lines[i])
    node_u = node.upper()
    i += 1

    if node_u == "ASSIGN":
        target, expr, i = _parse_assign(lines, i)
        return Stmt(kind="assign", step_id=step_id, data={"target": target, "expr": expr}), i
    if node_u == "RETURN":
        expr, i = _parse_required_expr_field(lines, i, field="EXPR")
        return Stmt(kind="return", step_id=step_id, data={"expr": expr}), i
    if node_u == "IF":
        cond, i = _parse_required_expr_field(lines, i, field="COND")
        then_block, i = _parse_required_block(lines, i, field="THEN")
        else_block, i = _parse_required_block(lines, i, field="ELSE")
        return (
            Stmt(kind="if", step_id=step_id, data={"cond": cond, "then": then_block, "else": else_block}),
            i,
        )
    if node_u == "LOOP":
        iter_val, i = _parse_required_scalar_field(lines, i, field="ITER")
        body_block, i = _parse_required_block(lines, i, field="BODY")
        return Stmt(kind="loop", step_id=step_id, data={"iter": iter_val, "body": body_block}), i

    raise IsuParseError(f"Unsupported node: {node}")


def _parse_stmt_head(line: str) -> tuple[Optional[str], str, Optional[str]]:
    if ":" not in line:
        raise IsuParseError(f"Invalid statement header: {line}")
    left, right = [p.strip() for p in line.split(":", 1)]
    if not left:
        raise IsuParseError("Empty statement key")

    step_id: Optional[str] = None
    node: str
    rest = right.strip()

    if _STEP_ID_RE.match(left):
        step_id = left
        if not rest:
            raise IsuParseError("Step ID line must include a node kind")
        parts = rest.split(maxsplit=1)
        node = parts[0]
        label = parts[1].strip() if len(parts) == 2 else None
        return step_id, node, label

    # In v0, we do not support forms like `ASSIGN:` or `IF "x":` as statement headers.
    if rest:
        # This likely looks like a field line rather than a statement header.
        raise IsuParseError(f"Invalid statement header (looks like a field line): {line}")

    node = left
    return None, node, None


def _parse_assign(lines: list[str], i: int) -> tuple[str, Expr, int]:
    target_val, i = _parse_required_scalar_field(lines, i, field="TARGET")
    expr, i = _parse_required_expr_field(lines, i, field="EXPR")
    if not isinstance(target_val, str):
        raise IsuParseError("TARGET must be a string")
    return target_val, expr, i


def _parse_required_scalar_field(lines: list[str], i: int, *, field: str) -> tuple[Any, int]:
    if i >= len(lines):
        raise IsuParseError(f"Missing required field: {field}")
    k, v = _split_kv(lines[i])
    if k.upper() != field:
        raise IsuParseError(f"Expected {field} but got {k}")
    return _parse_scalar(v), i + 1


def _parse_required_expr_field(lines: list[str], i: int, *, field: str) -> tuple[Expr, int]:
    if i >= len(lines):
        raise IsuParseError(f"Missing required field: {field}")
    k, v = _split_kv(lines[i])
    if k.upper() != field:
        raise IsuParseError(f"Expected {field} but got {k}")
    try:
        expr = parse_expr(v)
    except ValueError as e:
        raise IsuParseError(f"Invalid expression in {field}: {e}") from e
    return expr, i + 1


def _parse_required_block(lines: list[str], i: int, *, field: str) -> tuple[list[Stmt], int]:
    if i >= len(lines):
        raise IsuParseError(f"Missing required field: {field}")
    k, v = _split_kv(lines[i])
    if k.upper() != field:
        raise IsuParseError(f"Expected {field} but got {k}")
    if v.upper() != "BEGIN":
        raise IsuParseError(f"{field} must be followed by BEGIN")
    i += 1
    block_stmts, i = _parse_stmt_list(lines, i, until_end=True)
    return block_stmts, i


def _split_kv(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise IsuParseError(f"Invalid key/value line: {line}")
    k, v = [p.strip() for p in line.split(":", 1)]
    if not k:
        raise IsuParseError("Empty key")
    return k, v

