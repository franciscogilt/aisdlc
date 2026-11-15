"""Pruebas del generador. Uso (desde la raiz del repo):  python3 -m unittest discover -s tests -v"""
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("starterkit", ROOT / "starterkit.py")
sk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sk)

try:
    import yaml
except ImportError:  # PyYAML es opcional
    yaml = None

GIT = ["git", "-c", "user.email=t@example.com", "-c", "user.name=t"]


def generate(out, stack, db="postgres", cloud="aws", deploy="none", **kw):
    argv = ["--stack", stack, "--db", db, "--cloud", cloud, "--deploy", deploy, "--out", str(out)]
    for k, v in kw.items():
        argv += [f"--{k.replace('_', '-')}", str(v)] if v is not True else [f"--{k.replace('_', '-')}"]
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return sk.main(argv)


class CatalogTests(unittest.TestCase):
    def test_catalogs_are_consistent(self):
        self.assertEqual(set(sk.STACKS), set(sk.DEPS))
        self.assertEqual(set(sk.STACKS), set(sk._PIPE))
        self.assertEqual(len(sk.STACKS), 12)


class RenderTests(unittest.TestCase):
    def test_every_stack_renders_valid_files(self):
        for stack in sk.STACKS:
            for db in ("none", "postgres", "dynamodb"):
                with self.subTest(stack=stack, db=db):
                    for rel, content, mode, exe in sk.build_files("demo", stack, db, "aws", "vercel",
                                                                  "@org/team"):
                        self.assertNotIn("@@", content, f"{rel}: token sin renderizar")
                        if rel.endswith(".json"):
                            json.loads(content)
                        if yaml and rel.endswith((".yml", ".yaml")):
                            yaml.safe_load(content)

    def test_ci_has_required_jobs(self):
        for stack in sk.STACKS:
            ci = sk.ci_yml(stack, "postgres")
            self.assertIn("name: quality", ci)
            self.assertIn("name: secrets", ci)
            self.assertIn(sk.STACKS[stack]["test"], ci)

    def test_claude_md_has_dependency_policy(self):
        for stack in sk.STACKS:
            files = {f[0]: f[1] for f in sk.build_files("demo", stack, "none", "none", "none", "@o/t")}
            self.assertIn("No agregues librerias a menos que sea necesario", files["CLAUDE.md"])
            self.assertIn(sk.STACKS[stack]["test"], files["CLAUDE.md"])


class GeneratedKitTests(unittest.TestCase):
    def test_hook_evals_pass_for_every_stack(self):
        for stack in sk.STACKS:
            with self.subTest(stack=stack), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(generate(tmp, stack), 0)
                r = subprocess.run([sys.executable, "evals/run_hook_evals.py"], cwd=tmp,
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_hook_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate(tmp, "go")
            hook = pathlib.Path(tmp) / ".claude/hooks/protected_paths.py"
            env = {"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": tmp}
            r = subprocess.run([sys.executable, str(hook)], input="no-json", capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 2)
            (pathlib.Path(tmp) / ".claude/protected-paths.json").unlink()
            r = subprocess.run([sys.executable, str(hook)], input='{"tool_input":{"file_path":"/x/y.txt"}}',
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 2)

    def test_existing_files_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            (tmp / "CLAUDE.md").write_text("# mio\n")
            (tmp / "Dockerfile").write_text("FROM scratch\n")
            generate(tmp, "fastapi")
            self.assertEqual((tmp / "CLAUDE.md").read_text(), "# mio\n")
            self.assertEqual((tmp / "Dockerfile").read_text(), "FROM scratch\n")
            self.assertTrue((tmp / "CLAUDE.starter.md").exists())

    def test_update_refreshes_managed_and_keeps_owned(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            generate(tmp, "django")
            (tmp / "CLAUDE.md").write_text("# personalizado\n")
            (tmp / ".claude/hooks/protected_paths.py").write_text("# viejo\n")
            (tmp / ".github/workflows/ci.yml").write_text("name: mio\n")
            self.assertEqual(sk.main(["--update", "--out", str(tmp)]), 0)
            self.assertEqual((tmp / "CLAUDE.md").read_text(), "# personalizado\n")
            self.assertEqual((tmp / ".github/workflows/ci.yml").read_text(), "name: mio\n")
            self.assertIn("falla cerrado", (tmp / ".claude/hooks/protected_paths.py").read_text().lower())
            self.assertTrue((tmp / "CLAUDE.starter.md").exists())

    def test_update_requires_factory_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--update", "--out", tmp]), 2)

    def test_metrics_reads_git_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            generate(tmp, "express")
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            d = tmp / "intent/PED-1"
            d.mkdir(parents=True)
            (d / "intent.md").write_text("- **Estado:** aceptado\n")
            (d / "plan.md").write_text("## Pasos\n1. x\n\n## Desviaciones\nSe cambio el orden\n")
            subprocess.run(["git", "add", "intent"], cwd=tmp, check=True)
            subprocess.run(GIT + ["commit", "-q", "-m", "x"], cwd=tmp, check=True)
            r = subprocess.run([sys.executable, "scripts/metrics.py", "--json"], cwd=tmp, capture_output=True,
                               text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = json.loads(r.stdout)
            self.assertEqual(rows[0]["tarea"], "PED-1")
            self.assertEqual(rows[0]["estado"], "aceptado")
            self.assertEqual(rows[0]["desviaciones"], 1)


if __name__ == "__main__":
    unittest.main()
