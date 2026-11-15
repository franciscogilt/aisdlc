#!/usr/bin/env python3
"""Ejecuta, en orden, los pasos `run:` de un job de .github/workflows/ci.yml de un proyecto generado.
Sirve para comprobar que los comandos que genera el CI realmente funcionan (sin esperar a GitHub).
Las acciones `uses:` (setup-python, checkout...) se omiten: las sustituye tu entorno local.

  python3 tools/run_ci_locally.py PROYECTO [--job quality] [--venv DIR] [--skip NOMBRE ...]
Requiere PyYAML.
"""
import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

import yaml


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--job", default="quality")
    ap.add_argument("--venv", help="Crear/usar este virtualenv para los pasos (aisla pip)")
    ap.add_argument("--skip", action="append", default=[], help="Nombre (o parte) de un paso a omitir")
    a = ap.parse_args(argv)

    project = Path(a.project).resolve()
    wf = yaml.safe_load((project / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    job = wf["jobs"][a.job]
    env = dict(os.environ)
    env.update({k: str(v) for k, v in (job.get("env") or {}).items()})
    if a.venv:
        vdir = Path(a.venv).resolve()
        if not (vdir / "bin" / "python").exists():
            venv.create(vdir, with_pip=True)
        env["VIRTUAL_ENV"] = str(vdir)
        env["PATH"] = f"{vdir / 'bin'}{os.pathsep}{env['PATH']}"

    failed = []
    for step in job["steps"]:
        name = step.get("name") or step.get("uses") or "paso"
        if "run" not in step:
            print(f"-- omitido (accion): {name}")
            continue
        if any(s.lower() in name.lower() for s in a.skip):
            print(f"-- omitido (--skip): {name}")
            continue
        print(f"\n=== {name}", flush=True)
        r = subprocess.run(["bash", "-eo", "pipefail", "-c", step["run"]], cwd=project, env=env)
        if r.returncode != 0:
            print(f"!!! FALLO ({r.returncode}): {name}")
            failed.append(name)
            break
    print("\nResultado:", "FALLO en " + ", ".join(failed) if failed else "todos los pasos pasaron")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
