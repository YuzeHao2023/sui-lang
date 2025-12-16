"""
Pretty-printer for Isu (canonical text output).

v0 goals:
- Always generate identical text from identical Programs (deterministic output)
- Canonical Isu always includes Step IDs (to make AUTO_ID results visible)
"""

from __future__ import annotations

from typing import Any

from isu.ir import Expr, Program, Stmt


def pretty_print_isu(program: Program) -> str:
    """Convert a Program into canonical Isu text."""
    lines: list[str] = []

    def emit(s: str) -> None:
        lines.append(s)

    # Section order is fixed.
    if program.meta:
        emit("META:")
        for k in sorted(program.meta.keys()):
            emit(f"  {k}: {_scalar_to_str(program.meta[k])}")

    emit("FUNC:")
    for k in sorted(program.func.keys()):
        emit(f"  {k}: {_scalar_to_str(program.func[k])}")

    emit("IO:")
    for k in sorted(program.io.keys()):
        emit(f"  {k}: {_scalar_to_str(program.io[k])}")

    emit("STATE:")
    _emit_list(lines, program.state, indent="  ")

    emit("LOCAL:")
    _emit_list(lines, program.local, indent="  ")

    emit("STEPS:")
    emit("  SEQ: BEGIN")
    for s in _get_seq_children(program.steps):
        _emit_stmt(lines, s, indent="    ")
    emit("  END")

    return "\n".join(lines) + "\n"


def _emit_list(lines: list[str], items: list[Any], *, indent: str) -> None:
    if not items:
        lines.append(f"{indent}[]")
        return
    for v in items:
        lines.append(f"{indent}- {_scalar_to_str(v)}")


def _get_seq_children(stmt: Stmt) -> list[Stmt]:
    if stmt.kind != "seq":
        raise ValueError("STEPS root must be a seq node")
    return list(stmt.data.get("stmts", []))


def _emit_stmt(lines: list[str], stmt: Stmt, *, indent: str) -> None:
    if stmt.kind == "seq":
        raise ValueError("Nested seq is not supported in v0")

    step_id = stmt.step_id or "S?"
    if stmt.kind == "assign":
        lines.append(f"{indent}{step_id}: ASSIGN")
        lines.append(f"{indent}  TARGET: {stmt.data['target']}")
        lines.append(f"{indent}  EXPR: {_expr_to_str(stmt.data['expr'])}")
        return
    if stmt.kind == "return":
        lines.append(f"{indent}{step_id}: RETURN")
        lines.append(f"{indent}  EXPR: {_expr_to_str(stmt.data['expr'])}")
        return
    if stmt.kind == "if":
        lines.append(f"{indent}{step_id}: IF")
        lines.append(f"{indent}  COND: {_expr_to_str(stmt.data['cond'])}")
        lines.append(f"{indent}  THEN: BEGIN")
        for s in stmt.data["then"]:
            _emit_stmt(lines, s, indent=indent + "    ")
        lines.append(f"{indent}  END")
        lines.append(f"{indent}  ELSE: BEGIN")
        for s in stmt.data["else"]:
            _emit_stmt(lines, s, indent=indent + "    ")
        lines.append(f"{indent}  END")
        return
    if stmt.kind == "loop":
        lines.append(f"{indent}{step_id}: LOOP")
        lines.append(f"{indent}  ITER: {_scalar_to_str(stmt.data['iter'])}")
        lines.append(f"{indent}  BODY: BEGIN")
        for s in stmt.data["body"]:
            _emit_stmt(lines, s, indent=indent + "    ")
        lines.append(f"{indent}  END")
        return

    raise ValueError(f"Unsupported statement kind: {stmt.kind}")


def _expr_to_str(expr: Expr) -> str:
    def arg_to_str(a: Any) -> str:
        if isinstance(a, Expr):
            return _expr_to_str(a)
        return _scalar_to_str(a)

    args = " ".join(arg_to_str(a) for a in expr.args)
    return f"({expr.kind} {args})" if args else f"({expr.kind})"


def _scalar_to_str(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        # v0: quote only when whitespace is present (or for edge cases)
        if v == "" or any(ch.isspace() for ch in v) or v.startswith('"') or v.endswith('"'):
            escaped = v.replace("\\", "\\\\").replace('"', '\\"')
            return f"\"{escaped}\""
        return v
    if isinstance(v, list) and not v:
        return "[]"
    return str(v)

