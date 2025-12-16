import json

from isu import parse_isu, pretty_print_isu


def test_isu_roundtrip_is_deterministic_with_auto_id():
    src = """
; comment
META:
  AUTO_ID: true
FUNC:
  NAME: f
IO:
  INPUT: []
  OUTPUT: []
STATE:
  []
LOCAL:
  []
STEPS:
  SEQ: BEGIN
    ASSIGN:
      TARGET: x
      EXPR: (const 1)
    IF:
      COND: (lt (var x) (const 2))
      THEN: BEGIN
        RETURN:
          EXPR: (const 10)
      END
      ELSE: BEGIN
        RETURN:
          EXPR: (const 20)
      END
  END
"""
    p1 = parse_isu(src, do_canonicalize=True)
    out1 = pretty_print_isu(p1)
    p2 = parse_isu(out1, do_canonicalize=True)

    assert json.dumps(p1.to_json(), sort_keys=True) == json.dumps(p2.to_json(), sort_keys=True)


def test_auto_id_assigns_step_ids():
    src = """
META:
  AUTO_ID: true
FUNC:
  NAME: f
IO:
  INPUT: []
  OUTPUT: []
STATE:
  []
LOCAL:
  []
STEPS:
  SEQ: BEGIN
    ASSIGN:
      TARGET: x
      EXPR: (const 1)
    RETURN:
      EXPR: (var x)
  END
"""
    p = parse_isu(src, do_canonicalize=True)
    out = pretty_print_isu(p)
    assert "S1: ASSIGN" in out
    assert "S2: RETURN" in out

