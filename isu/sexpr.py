"""
Tokenizer and parser for S-expressions (prefix notation).

In v0 we deliberately drop infix expressions to eliminate ambiguity.
"""

from __future__ import annotations

from typing import Any

from isu.ir import Expr


def tokenize_sexpr(src: str) -> list[str]:
    """Tokenize an S-expression into tokens (parens, strings, symbols)."""
    tokens: list[str] = []
    i = 0
    s = src.strip()
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in ("(", ")"):
            tokens.append(c)
            i += 1
            continue
        if c == '"':
            j = i + 1
            buf = ['"']
            while j < len(s):
                ch = s[j]
                buf.append(ch)
                if ch == "\\":
                    j += 1
                    if j < len(s):
                        buf.append(s[j])
                        j += 1
                    continue
                if ch == '"':
                    break
                j += 1
            if not buf or buf[-1] != '"':
                raise ValueError("Unterminated string literal")
            tokens.append("".join(buf))
            i = j + 1
            continue

        # Symbol / number
        j = i
        while j < len(s) and (not s[j].isspace()) and s[j] not in ("(", ")"):
            j += 1
        tokens.append(s[i:j])
        i = j
    return tokens


class _TokenStream:
    def __init__(self, tokens: list[str]):
        self._tokens = tokens
        self._i = 0

    def peek(self) -> str | None:
        if self._i >= len(self._tokens):
            return None
        return self._tokens[self._i]

    def pop(self) -> str:
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of tokens")
        self._i += 1
        return tok


_OP_KIND_MAP: dict[str, str] = {
    "const": "const",
    "var": "var",
    "add": "add",
    "sub": "sub",
    "mul": "mul",
    "div": "div",
    "mod": "mod",
    "eq": "eq",
    "ne": "ne",
    "lt": "lt",
    "le": "le",
    "gt": "gt",
    "ge": "ge",
    "index": "index",
    "call": "call",
}


def parse_expr(src: str) -> Expr:
    """Parse an S-expression string into an Expr."""
    tokens = tokenize_sexpr(src)
    stream = _TokenStream(tokens)
    expr = _parse_expr_stream(stream)
    if stream.peek() is not None:
        raise ValueError("Extra tokens after expression")
    return expr


def _parse_atom(tok: str) -> Any:
    if tok.startswith('"') and tok.endswith('"'):
        # v0: strings are double-quoted
        return tok[1:-1]
    if tok == "true":
        return True
    if tok == "false":
        return False
    # Numbers (prefer int, fallback to float)
    try:
        if "." in tok:
            return float(tok)
        return int(tok)
    except ValueError:
        return tok


def _parse_expr_stream(stream: _TokenStream) -> Expr:
    tok = stream.pop()
    if tok != "(":
        raise ValueError("Expression must start with '('")
    op = stream.pop()
    if op not in _OP_KIND_MAP:
        raise ValueError(f"Unsupported operator: {op}")

    args: list[Any] = []
    while True:
        nxt = stream.peek()
        if nxt is None:
            raise ValueError("Unterminated expression")
        if nxt == ")":
            stream.pop()
            break
        if nxt == "(":
            args.append(_parse_expr_stream(stream))
        else:
            args.append(_parse_atom(stream.pop()))

    return Expr(kind=_OP_KIND_MAP[op], args=tuple(args))

