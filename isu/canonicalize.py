"""
Canonicalization for Isu.

- Stable Step ID assignment based on AUTO_ID
- Minimal processing to keep outputs deterministic
"""

from __future__ import annotations

from isu.ir import Program, Stmt


def canonicalize(program: Program) -> Program:
    """Canonicalize the whole program."""
    auto_id = bool(program.meta.get("AUTO_ID", False))
    steps = _canonicalize_steps(program.steps, auto_id=auto_id)
    return Program(
        meta=dict(program.meta),
        func=dict(program.func),
        io=dict(program.io),
        state=list(program.state),
        local=list(program.local),
        steps=steps,
    )


def _canonicalize_steps(root: Stmt, auto_id: bool) -> Stmt:
    counter = {"n": 0}

    def next_id() -> str:
        counter["n"] += 1
        return f"S{counter['n']}"

    def walk(stmt: Stmt) -> Stmt:
        # The seq container itself does not have a Step ID (children do).
        if stmt.kind == "seq":
            children = [walk(s) for s in stmt.data.get("stmts", [])]
            data = dict(stmt.data)
            data["stmts"] = children
            return Stmt(kind="seq", step_id=None, data=data)

        # Nodes with child blocks
        data = dict(stmt.data)
        for key in ("then", "else", "body"):
            if key in data and isinstance(data[key], list):
                data[key] = [walk(s) for s in data[key]]

        step_id = stmt.step_id
        if step_id is None and auto_id:
            step_id = next_id()
        elif step_id is None and not auto_id:
            # Step IDs are required in canonical form. In v0, we leave this to the validator.
            step_id = None

        return Stmt(kind=stmt.kind, step_id=step_id, data=data)

    return walk(root)

