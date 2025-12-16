"""
Isu (structured pseudocode) implementation.

This package provides the minimal v0 pipeline:
- Deterministic parsing from Isu text to S-IR (JSON-compatible AST)
- Canonicalization (e.g., AUTO_ID)
- Pretty-printing back to canonical Isu
"""

from isu.parser import parse_isu  # noqa: F401
from isu.pretty import pretty_print_isu  # noqa: F401

