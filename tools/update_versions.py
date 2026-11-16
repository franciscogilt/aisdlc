#!/usr/bin/env python3
"""
Actualiza las versiones que el generador lleva fijadas, consultando los registros publicos.

  RT (runtimes)        <- endoflife.date: ultimo ciclo NO EOL, con >= 60 dias desde su lanzamiento
                          y, en Node/Java/.NET, solo LTS vigentes
  GitHub Actions       <- ultimo release de cada Action (se usa la version mayor, p. ej. v5)
  starter_apps pins    <- PyPI (ultima version estable de cada paquete fijado con ==)

Uso:
  python3 tools/update_versions.py            # muestra los cambios (no escribe)
  python3 tools/update_versions.py --write    # aplica los cambios
  python3 tools/update_versions.py --check    # exit 1 si hay algo desactualizado
  python3 tools/update_versions.py --strict   # exit 3 si alguna consulta falla (para CI)
Variable opcional GITHUB_TOKEN (evita limites de la API de GitHub).
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
STARTERKIT = ROOT / "starterkit.py"
MIN_AGE_DAYS = 60

# clave de RT -> (producto en endoflife.date, solo LTS)
RUNTIMES = {
    "python": ("python", False), "node": ("nodejs", True), "java": ("eclipse-temurin", True),
    "dotnet": ("dotnet", True), "go": ("go", False), "ruby": ("ruby", False),
    "php": ("php", False), "postgres": ("postgresql", False),
}
ACTIONS = [
    "actions/checkout", "actions/setup-python", "actions/setup-node", "actions/setup-java",
    "actions/setup-dotnet", "actions/setup-go", "ruby/setup-ruby", "shivammathur/setup-php",
    "github/codeql-action", "anthropics/claude-code-action",
    "aws-actions/configure-aws-credentials", "aws-actions/amazon-ecr-login", "azure/login",
    "google-github-actions/auth", "google-github-actions/setup-gcloud",
]


def fetch_json(url):
    headers = {"User-Agent": "aisdlc-update-versions", "Accept": "application/json"}
    if "api.github.com" in url and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def _date(value):
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        return None


def _key(cycle):
    return tuple(int(p) if p.isdigit() else 0 for p in re.split(r"[.\-]", str(cycle)))


def pick_cycle(cycles, only_lts, today):
    """Elige el ciclo mas nuevo que sea estable: no EOL, lanzado hace >= MIN_AGE_DAYS y (si aplica) LTS."""
    best = []
    for c in cycles:
        eol = c.get("eol")
        if eol is True or (isinstance(eol, str) and (_date(eol) or dt.date.max) <= today):
            continue
        released = _date(c.get("releaseDate"))
        if not released or (today - released).days < MIN_AGE_DAYS:
            continue
        lts = c.get("lts")
        is_lts = lts is True or (isinstance(lts, str) and (_date(lts) or dt.date.max) <= today)
        if only_lts and not is_lts:
            continue
        best.append(str(c["cycle"]))
    return max(best, key=_key) if best else None


def major_of(tag):
    """'v5.0.1' o '2.36.0' -> 'v5' / 'v2'. Ignora tags que no son una version (p. ej. 'codeql-bundle-v2.1')."""
    m = re.match(r"^v?(\d+)(?:\.\d+)*$", tag or "")
    return f"v{m.group(1)}" if m else None


def normalize(key, cycle):
    """endoflife.date a veces da .NET como '10'; las imagenes y setup-dotnet usan '10.0'."""
    return f"{cycle}.0" if key == "dotnet" and "." not in cycle else cycle


def latest_runtimes(today, errors):
    out = {}
    for key, (product, only_lts) in RUNTIMES.items():
        try:
            cycle = pick_cycle(fetch_json(f"https://endoflife.date/api/{product}.json"), only_lts, today)
            if cycle:
                out[key] = normalize(key, cycle)
            else:
                errors.append(f"{product}: ningun ciclo cumple los criterios")
        except Exception as exc:
            errors.append(f"{product}: {exc}")
    return out


def latest_major(repo):
    """Version mayor del release estable mas reciente (la API de 'latest' puede devolver bundles u otros tags)."""
    for rel in fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page=30"):
        if rel.get("draft") or rel.get("prerelease"):
            continue
        major = major_of(rel.get("tag_name"))
        if major:
            return major
    return None


def latest_actions(errors):
    out = {}
    for repo in ACTIONS:
        try:
            major = latest_major(repo)
            if major:
                out[repo] = major
            else:
                errors.append(f"{repo}: ningun release estable con formato de version")
        except Exception as exc:
            errors.append(f"{repo}: {exc}")
    return out


def latest_pypi(package):
    return fetch_json(f"https://pypi.org/pypi/{package}/json")["info"]["version"]


def plan_starterkit(text, runtimes, actions):
    """Devuelve (texto_nuevo, cambios) para starterkit.py."""
    changes = []
    for key, new in runtimes.items():
        m = re.search(rf'(\b{key}=")([^"]*)(")', text)
        if m and m.group(2) != new:
            changes.append(f"RT.{key}: {m.group(2)} -> {new}")
            text = text[:m.start(2)] + new + text[m.end(2):]
    for repo, major in actions.items():
        def sub(m, major=major, repo=repo):
            if m.group(2) != major:
                changes.append(f"{m.group(1)}: {m.group(2)} -> {major}")
            return f"{m.group(1)}@{major}"
        text = re.sub(rf"({re.escape(repo)}(?:/[a-z-]+)?)@(v\d+)", sub, text)
    return text, sorted(set(changes))


def plan_pins(path, lookup):
    old = path.read_text(encoding="utf-8")
    changes, lines = [], []
    for line in old.splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+(?:\[[^\]]+\])?)==(\S+)$", line)
        if m:
            name = re.sub(r"\[.*\]", "", m.group(1))
            new = lookup(name)
            if new != m.group(2):
                changes.append(f"{path.relative_to(ROOT)}: {name} {m.group(2)} -> {new}")
                line = f"{m.group(1)}=={new}"
        lines.append(line)
    return "\n".join(lines) + "\n", changes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--skip", action="append", default=[], choices=["runtimes", "actions", "pins"])
    a = ap.parse_args(argv)
    today, errors, changes = dt.date.today(), [], []

    writes = {}
    text = STARTERKIT.read_text(encoding="utf-8")
    runtimes = {} if "runtimes" in a.skip else latest_runtimes(today, errors)
    actions = {} if "actions" in a.skip else latest_actions(errors)
    new_text, ch = plan_starterkit(text, runtimes, actions)
    if ch:
        writes[STARTERKIT] = new_text
        changes += ch

    if "pins" not in a.skip:
        cache = {}

        def lookup(pkg):
            if pkg not in cache:
                try:
                    cache[pkg] = latest_pypi(pkg)
                except Exception as exc:
                    errors.append(f"PyPI {pkg}: {exc}")
                    cache[pkg] = None
            return cache[pkg]

        for req in sorted((ROOT / "starter_apps").glob("*/requirements*.txt")):
            def safe(pkg):
                return lookup(pkg) or current.get(pkg)
            current = {m.group(1): m.group(2) for l in req.read_text().splitlines()
                       if (m := re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?==(\S+)$", l))}
            new, ch = plan_pins(req, safe)
            if ch:
                writes[req] = new
                changes += ch

    for c in changes:
        print("  ~", c)
    for e in errors:
        print("  ! no se pudo consultar:", e, file=sys.stderr)
    print(f"\n{len(changes)} cambio(s), {len(errors)} consulta(s) fallida(s).")
    if a.write:
        for path, content in writes.items():
            path.write_text(content, encoding="utf-8")
    if a.strict and errors:
        return 3
    if a.check and changes:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
