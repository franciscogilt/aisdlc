#!/usr/bin/env python3
"""Decide que stacks debe probar el workflow E2E segun los archivos cambiados (para gastar menos minutos de Actions).

- push a main, ejecucion manual o programada: los 12 stacks.
- PR que toca el generador, tools/ o el propio E2E: los 12 (afecta a todos).
- PR que solo toca starter_apps/<stack>/: solo esos stacks.
- PR que solo toca documentacion, tests u otros archivos: ninguno.

Uso: e2e_plan.py EVENTO [ARCHIVO...]  -> imprime el JSON {"include": [...]}"""
import json
import sys

# Fuente unica de verdad del matrix: stack, puerto de la app y si guarda en Postgres.
STACKS = [
    {"stack": "fastapi", "port": 8000, "db": True},
    {"stack": "django", "port": 8000, "db": True},
    {"stack": "express", "port": 3000, "db": True},
    {"stack": "dotnet", "port": 8080, "db": True},
    {"stack": "springboot", "port": 8080, "db": True},
    {"stack": "go", "port": 8080, "db": False},
    {"stack": "nextjs", "port": 3000, "db": False},
    {"stack": "react", "port": 8080, "db": False},
    {"stack": "angular", "port": 8080, "db": False},
    {"stack": "laravel", "port": 8000, "db": True},
    {"stack": "rails", "port": 3000, "db": False},
    {"stack": "quarkus", "port": 8080, "db": True},
]
ALWAYS_FULL_EVENTS = {"push", "workflow_dispatch", "schedule"}
SHARED = ("starterkit.py", "tools/", ".github/workflows/e2e.yml")


def plan(event, changed):
    if event in ALWAYS_FULL_EVENTS or any(f.startswith(SHARED) for f in changed):
        return list(STACKS)
    touched = {f.split("/")[1] for f in changed if f.startswith("starter_apps/") and f.count("/") >= 2}
    return [s for s in STACKS if s["stack"] in touched]


if __name__ == "__main__":
    print(json.dumps({"include": plan(sys.argv[1], sys.argv[2:])}))
