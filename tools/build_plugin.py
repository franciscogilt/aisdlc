#!/usr/bin/env python3
"""Genera el plugin compartido (plugin/ y .claude-plugin/marketplace.json) desde las plantillas de starterkit.py.
Una sola fuente de verdad: las skills, el verificador y los comandos se editan en starterkit.py.

  python3 tools/build_plugin.py           # escribe los archivos
  python3 tools/build_plugin.py --check   # exit 1 si el plugin esta desactualizado (para CI)
"""
import importlib.util
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("starterkit", ROOT / "starterkit.py")
sk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sk)


def main():
    files = sk.plugin_files()
    if "--check" in sys.argv:
        stale = [rel for rel, content in files.items()
                 if not (ROOT / rel).exists() or (ROOT / rel).read_text(encoding="utf-8") != content]
        extra = [str(p.relative_to(ROOT)) for p in (ROOT / "plugin").rglob("*")
                 if p.is_file() and str(p.relative_to(ROOT)) not in files]
        for rel in stale:
            print(f"desactualizado: {rel}")
        for rel in extra:
            print(f"sobrante: {rel}")
        if stale or extra:
            print("Ejecuta: python3 tools/build_plugin.py")
            return 1
        print("plugin al dia")
        return 0
    shutil.rmtree(ROOT / "plugin", ignore_errors=True)
    for rel, content in files.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"{len(files)} archivos escritos en plugin/ y .claude-plugin/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
