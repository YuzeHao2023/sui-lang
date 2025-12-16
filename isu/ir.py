"""
Minimal internal representation (S-IR) for Isu.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


ExprKind = Literal[
    "const",
    "var",
    "add",
    "sub",
    "mul",
    "div",
    "mod",
    "eq",
    "ne",
    "lt",
    "le",
    "gt",
    "ge",
    "index",
    "call",
]


@dataclass(frozen=True, slots=True)
class Expr:
    """Expression node (S-expression)."""

    kind: ExprKind
    args: tuple[Any, ...]

    def to_json(self) -> dict[str, Any]:
        """Convert to a JSON-compatible dict (deterministic shape)."""
        return {
            "kind": self.kind,
            "args": [self._arg_to_json(a) for a in self.args],
        }

    @staticmethod
    def _arg_to_json(arg: Any) -> Any:
        if isinstance(arg, Expr):
            return arg.to_json()
        return arg


StmtKind = Literal["seq", "assign", "if", "loop", "return"]


@dataclass(frozen=True, slots=True)
class Stmt:
    """Statement node."""

    kind: StmtKind
    step_id: Optional[str]
    data: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        """Convert to a JSON-compatible dict (deterministic shape)."""
        # Even though Python preserves dict insertion order, we sort keys explicitly for determinism.
        return {
            "kind": self.kind,
            "step_id": self.step_id,
            "data": {k: self._val_to_json(self.data[k]) for k in sorted(self.data.keys())},
        }

    @staticmethod
    def _val_to_json(val: Any) -> Any:
        if isinstance(val, Expr):
            return val.to_json()
        if isinstance(val, Stmt):
            return val.to_json()
        if isinstance(val, list):
            return [Stmt._val_to_json(v) for v in val]
        return val


@dataclass(frozen=True, slots=True)
class Program:
    """Minimal Isu program container."""

    meta: dict[str, Any]
    func: dict[str, Any]
    io: dict[str, Any]
    state: list[Any]
    local: list[Any]
    steps: Stmt

    def to_json(self) -> dict[str, Any]:
        """Convert to a JSON-serializable S-IR dict."""
        return {
            "meta": {k: self.meta[k] for k in sorted(self.meta.keys())},
            "func": {k: self.func[k] for k in sorted(self.func.keys())},
            "io": {k: self.io[k] for k in sorted(self.io.keys())},
            "state": list(self.state),
            "local": list(self.local),
            "steps": self.steps.to_json(),
        }

