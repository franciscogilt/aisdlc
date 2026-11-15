#!/usr/bin/env python3
# ruff: noqa
"""Metricas del flujo a partir de Git: por tarea (intent/<ID>/) calcula tiempo de ciclo, commits
y desviaciones del plan. Uso (desde la raiz del repo):  python3 scripts/metrics.py [--json]"""
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def deviations(plan):
    if not plan.exists():
        return None
    m = re.search(r"## Desviaciones\s*\n(.*?)(\n## |\Z)", plan.read_text(encoding="utf-8"), re.S)
    lines = [l.strip() for l in (m.group(1) if m else "").splitlines() if l.strip()]
    return len([l for l in lines if l.lower() not in ("(ninguna)", "ninguna", "-")])


def main():
    root = pathlib.Path("intent")
    rows = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")) if root.exists() else []:
        stamps = [int(x) for x in git("log", "--format=%ct", "--", str(d)).split()]
        if not stamps:
            continue
        intent = (d / "intent.md").read_text(encoding="utf-8") if (d / "intent.md").exists() else ""
        status = re.search(r"\*\*Estado:\*\*\s*(\w+)", intent)
        rows.append({
            "tarea": d.name,
            "estado": status.group(1) if status else "?",
            "commits": len(stamps),
            "dias_ciclo": round((max(stamps) - min(stamps)) / 86400, 2),
            "primer_commit": dt.datetime.fromtimestamp(min(stamps), dt.timezone.utc).strftime("%Y-%m-%d"),
            "tiene_spec": (d / "spec.md").exists(),
            "tiene_plan": (d / "plan.md").exists(),
            "desviaciones": deviations(d / "plan.md"),
        })
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("Sin tareas en intent/<ID>/ con historial en Git.")
        return
    print(f"{'tarea':<16}{'estado':<12}{'commits':>8}{'dias':>8}{'spec':>6}{'plan':>6}{'desv':>6}")
    for r in rows:
        print(f"{r['tarea']:<16}{r['estado']:<12}{r['commits']:>8}{r['dias_ciclo']:>8}"
              f"{'si' if r['tiene_spec'] else 'no':>6}{'si' if r['tiene_plan'] else 'no':>6}{str(r['desviaciones']):>6}")
    cyc = [r["dias_ciclo"] for r in rows]
    print(f"\n{len(rows)} tareas | ciclo medio {sum(cyc) / len(cyc):.2f} dias")


if __name__ == "__main__":
    main()
