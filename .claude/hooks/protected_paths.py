#!/usr/bin/env python3
# ruff: noqa
"""
PreToolUse gate de la fabrica. Falla CERRADO.

Cubre Edit/Write/MultiEdit (archivos) y Bash (heuristicas de shell).
- Ruta protegida sin ticket CHG-#### en la rama -> bloquea (exit 2).
- Ruta protegida con ticket                      -> pide aprobacion humana ("ask").
- Secretos (.env), manifiestos de dependencias   -> piden aprobacion.
- Comandos destructivos / instalar paquetes      -> bloquean o piden aprobacion.
- Cualquier error inesperado                     -> bloquea (exit 2).
  (exit 1 NO bloquea en Claude Code: el script nunca debe terminar con 1)
Las comprobaciones de Bash son heuristicas, no un sandbox: complementalas con
las reglas de permisos de settings.json y con proteccion de ramas en GitHub.
"""
import json
import os
import re
import subprocess
import sys


def block(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def ask(msg):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": msg,
    }}))
    sys.exit(0)


def branch_name():
    project = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    out = subprocess.run(["git", "-C", project, "rev-parse", "--abbrev-ref", "HEAD"],
                         capture_output=True, text=True, timeout=5)
    return out.stdout.strip() if out.returncode == 0 else ""


def ticket_gate(what):
    t = re.search(r"CHG-\d+", branch_name())
    if not t:
        block(f"Ruta protegida ({what}). Crea una rama con ticket de cambio, "
              "por ejemplo feat/CHG-1234-descripcion, y reintenta.")
    ask(f"Ruta protegida bajo {t.group(0)} ({what}). Un humano debe aprobar.")


DEP_MSG = ("Cambio de dependencias. Solo si es necesario: debe ser la libreria mas popular y "
           "actualizada de su categoria, con version estable verificada y justificada.")

BLOCK_PATTERNS = [
    r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+(/|~|\$HOME|\*)(\s|$|/\*)",
    r"\bgit\s+push\b.*(--force\b|--force-with-lease\b|\s-f\b)",
    r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(sh|bash|zsh)\b",
    r"\bchmod\s+-R\s+777\b",
    r":\(\)\s*\{",
]
ASK_PATTERNS = [
    r"\bterraform\s+(apply|destroy)\b",
    r"\bgit\s+push\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bdocker\s+compose\s+down\s+(-\S*v|--volumes)",
    r"\b(aws|az|gcloud)\b.*\b(delete|terminate|remove|destroy)",
    r"\baws\s+s3\s+(rm|rb)\b",
    r"\bkubectl\s+(delete|apply)\b",
    r"\b(drop|truncate)\s+(table|database)\b",
]
WRITE_HINT = re.compile(r"(>>?|\bsed\s+-i|\btee\b|\bmv\b|\bcp\b|\brm\b|\bperl\s+-\w*i|\btruncate\b"
                        r"|\bgit\s+(checkout|restore)\b)")
ENV_READ = re.compile(r"(?<![\w./-])(cat|less|more|head|tail|cp|mv|source)\s+[^|;&]*\.env"
                      r"(?!\.(?:example|sample))\b")


def check_file(path, cfg):
    path = path.replace("\\", "/")
    base = os.path.basename(path)
    if any(base == s or base.startswith(s + ".") for s in cfg.get("secrets", [])):
        if base.endswith((".example", ".sample")):
            sys.exit(0)
        ask(f"Archivo de secretos ({base}). Un humano debe aprobar esta edicion.")
    for dep in cfg.get("dependencies", []):
        if base == dep or (dep.startswith("*") and base.endswith(dep[1:])):
            ask(f"{DEP_MSG} ({base})")
    if any(p in path for p in cfg.get("protected", [])):
        ticket_gate(path)
    sys.exit(0)


def check_bash(cmd, cfg):
    flat = re.sub(r"\d*>&\d+|\d*>\s*/dev/null", "", cmd)
    for pat in BLOCK_PATTERNS:
        if re.search(pat, flat):
            block(f"Comando bloqueado por seguridad: {cmd[:120]}")
    if WRITE_HINT.search(flat):
        for p in cfg.get("protected", []):
            if p in flat:
                ticket_gate(f"comando de shell sobre {p}")
    if ENV_READ.search(flat):
        ask("El comando lee o copia un archivo de secretos (.env). Un humano debe aprobar.")
    for pat in cfg.get("install_patterns", []):
        if re.search(pat, flat):
            ask(DEP_MSG)
    for pat in ASK_PATTERNS:
        if re.search(pat, flat, re.I):
            ask(f"Comando sensible, requiere aprobacion humana: {cmd[:120]}")
    sys.exit(0)


def main():
    data = json.load(sys.stdin)
    ti = data.get("tool_input") or {}
    project = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    with open(os.path.join(project, ".claude", "protected-paths.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    if data.get("tool_name") == "Bash" or ("command" in ti and "file_path" not in ti):
        check_bash(ti.get("command") or "", cfg)
    path = ti.get("file_path") or ""
    if not path:
        sys.exit(0)
    check_file(path, cfg)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException as exc:  # falla cerrado
        sys.stderr.write(f"protected_paths hook fallo ({exc!r}); se bloquea por seguridad.\n")
        sys.exit(2)
