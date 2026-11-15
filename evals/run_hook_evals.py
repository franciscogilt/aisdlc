#!/usr/bin/env python3
# ruff: noqa
"""Evals deterministas del hook: cada caso dice si debe bloquear, pedir aprobacion o permitir.
Uso: python3 evals/run_hook_evals.py     (exit 0 = todo bien)"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude" / "hooks" / "protected_paths.py"
cases = json.loads((ROOT / "evals" / "hook_cases.json").read_text(encoding="utf-8"))


def classify(r):
    if r.returncode == 2:
        return "block"
    if r.returncode == 0:
        return "ask" if '"permissionDecision": "ask"' in r.stdout else "allow"
    return f"error(exit={r.returncode})"


failed = 0
for c in cases:
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(ROOT / ".claude", pathlib.Path(tmp) / ".claude")
        git = ["git", "-C", tmp, "-c", "user.email=ci@example.com", "-c", "user.name=ci"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["checkout", "-q", "-b", c["branch"]], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "init"], check=True)
        if "raw" in c:
            stdin = c["raw"]
        else:
            ti = {k: v.replace("$PROJECT", tmp) for k, v in c["input"].items()}
            stdin = json.dumps({"tool_name": c["tool"], "tool_input": ti})
        r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin:/usr/local/bin", "CLAUDE_PROJECT_DIR": tmp})
        got = classify(r)
        ok = got == c["expect"]
        failed += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {c['name']}: esperado={c['expect']} obtenido={got}")
print(f"\n{len(cases) - failed}/{len(cases)} casos correctos")
sys.exit(1 if failed else 0)
