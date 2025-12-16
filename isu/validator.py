"""
Minimal static validation for Isu.

In v0 we prioritize clear failure signals (what is wrong and where),
in addition to deterministic parsing.
"""

from __future__ import annotations

from dataclasses import dataclass

from isu.ir import Program, Stmt


@dataclass(frozen=True, slots=True)
class StaticError:
    """Minimal static error container."""

    message: str
    step_id: str | None = None


def validate(program: Program) -> list[StaticError]:
    """Validate a Program and return a list of errors (empty means OK)."""
    errors: list[StaticError] = []

    auto_id = bool(program.meta.get("AUTO_ID", False))

    seen: set[str] = set()

    def check_stmt(stmt: Stmt) -> None:
        if stmt.kind == "seq":
            for s in stmt.data.get("stmts", []):
                check_stmt(s)
            return

        if not auto_id and not stmt.step_id:
            errors.append(StaticError(message="Step ID is required (AUTO_ID=false)"))
        if stmt.step_id:
            if stmt.step_id in seen:
                errors.append(StaticError(message="Duplicate Step ID", step_id=stmt.step_id))
            seen.add(stmt.step_id)

        for key in ("then", "else", "body"):
            if key in stmt.data and isinstance(stmt.data[key], list):
                for s in stmt.data[key]:
                    check_stmt(s)

    check_stmt(program.steps)
    return errors

