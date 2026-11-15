#!/usr/bin/env python3
# ruff: noqa
"""EXPERIMENTAL. Evals de comportamiento: corren `claude -p` y revisan la respuesta.
Requieren Claude Code instalado y autenticado (consumen uso). Corre estos casos al cambiar
CLAUDE.md, skills o el modelo; agrega un caso nuevo cada vez que descubras un error real.
Uso: python3 evals/run_behavior_evals.py"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
cases = json.loads((ROOT / "evals" / "behavior_cases.json").read_text(encoding="utf-8"))
failed = 0
for c in cases:
    r = subprocess.run(["claude", "-p", c["prompt"], "--output-format", "json",
                        "--permission-mode", "plan"], cwd=ROOT, capture_output=True, text=True, timeout=600)
    try:
        out = json.loads(r.stdout).get("result", "").lower()
    except ValueError:
        out = ""
    has_any = any(s.lower() in out for s in c.get("must_contain_any", [])) if c.get("must_contain_any") else True
    has_bad = any(s.lower() in out for s in c.get("must_not_contain", []))
    ok = has_any and not has_bad
    failed += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {c['name']}")
sys.exit(1 if failed else 0)
