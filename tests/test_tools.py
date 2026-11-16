"""Pruebas de las herramientas nuevas: versiones automaticas, plugin compartido y app de arranque."""
import ast
import datetime as dt
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sk = load("starterkit", "starterkit.py")
uv = load("update_versions", "tools/update_versions.py")
TODAY = dt.date(2026, 11, 15)


def cyc(cycle, released, eol=False, lts=False):
    return {"cycle": cycle, "releaseDate": released, "eol": eol, "lts": lts}


class PickCycleTests(unittest.TestCase):
    def test_skips_eol_and_too_recent(self):
        cycles = [cyc("3.15", "2026-10-01"),            # muy reciente (< 60 dias)
                  cyc("3.14", "2025-10-07"),
                  cyc("3.13", "2024-10-07"),
                  cyc("3.9", "2020-10-05", eol="2025-10-31")]
        self.assertEqual(uv.pick_cycle(cycles, False, TODAY), "3.14")

    def test_lts_only(self):
        cycles = [cyc("25", "2025-10-15", lts="2025-10-28"), cyc("24", "2025-05-06", eol="2026-01-01"),
                  cyc("26", "2026-05-01", lts="2026-12-01"),    # aun no es LTS
                  cyc("22", "2024-04-24", lts="2024-10-29")]
        self.assertEqual(uv.pick_cycle(cycles, True, TODAY), "25")

    def test_numeric_ordering(self):
        cycles = [cyc("9", "2020-01-01"), cyc("17", "2024-01-01"), cyc("10", "2021-01-01")]
        self.assertEqual(uv.pick_cycle(cycles, False, TODAY), "17")

    def test_nothing_eligible(self):
        self.assertIsNone(uv.pick_cycle([cyc("1", "2026-11-01")], False, TODAY))

    def test_major_of(self):
        self.assertEqual(uv.major_of("v5.0.1"), "v5")
        self.assertEqual(uv.major_of("2.36.0"), "v2")      # setup-php publica tags sin 'v'
        self.assertIsNone(uv.major_of("codeql-bundle-v2.1"))
        self.assertIsNone(uv.major_of(None))

    def test_latest_major_skips_bundles_and_prereleases(self):
        releases = [{"tag_name": "codeql-bundle-v2.9.0"}, {"tag_name": "v4.0.0-rc1", "prerelease": True},
                    {"tag_name": "v3.30.1"}, {"tag_name": "v3.30.0"}]
        original = uv.fetch_json
        uv.fetch_json = lambda url: releases
        try:
            self.assertEqual(uv.latest_major("github/codeql-action"), "v3")
        finally:
            uv.fetch_json = original

    def test_dotnet_is_normalized(self):
        self.assertEqual(uv.normalize("dotnet", "10"), "10.0")
        self.assertEqual(uv.normalize("dotnet", "10.0"), "10.0")
        self.assertEqual(uv.normalize("node", "24"), "24")


class PlanTests(unittest.TestCase):
    def test_plan_starterkit_updates_runtimes_and_actions(self):
        text = ('RT = dict(python="3.12", node="24")\n'
                '_step("actions/setup-python@v4")\n- uses: github/codeql-action/init@v2\n')
        new, changes = uv.plan_starterkit(text, {"python": "3.14", "node": "24"},
                                          {"actions/setup-python": "v5", "github/codeql-action": "v3"})
        self.assertIn('python="3.14"', new)
        self.assertIn("setup-python@v5", new)
        self.assertIn("codeql-action/init@v3", new)
        self.assertEqual(len(changes), 3)

    def test_plan_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            sa = pathlib.Path(tmp) / "starter_apps" / "x"
            sa.mkdir(parents=True)
            req = sa / "requirements.txt"
            req.write_text("fastapi==0.1.0\n-r other.txt\nuvicorn[standard]==0.2.0\n")
            old_root = uv.ROOT
            uv.ROOT = pathlib.Path(tmp)
            try:
                new, changes = uv.plan_pins(req, lambda pkg: {"fastapi": "9.9.9", "uvicorn": "0.2.0"}[pkg])
            finally:
                uv.ROOT = old_root
            self.assertIn("fastapi==9.9.9", new)
            self.assertIn("uvicorn[standard]==0.2.0", new)
            self.assertIn("-r other.txt", new)
            self.assertEqual(len(changes), 1)

    def test_current_pins_in_repo_are_exact(self):
        for req in (ROOT / "starter_apps").glob("*/requirements*.txt"):
            for line in req.read_text().splitlines():
                self.assertTrue(line.startswith("-r ") or "==" in line, f"{req}: {line!r} sin version fija")
                self.assertNotIn("0.0.0", line)


class PluginTests(unittest.TestCase):
    def test_plugin_is_in_sync_with_templates(self):
        r = subprocess.run([sys.executable, "tools/build_plugin.py", "--check"], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_plugin_manifests(self):
        files = sk.plugin_files()
        plugin = json.loads(files["plugin/.claude-plugin/plugin.json"])
        market = json.loads(files[".claude-plugin/marketplace.json"])
        self.assertEqual(plugin["name"], "aisdlc")
        self.assertEqual(market["plugins"][0]["source"], "./plugin")
        self.assertIn("plugin/agents/verifier.md", files)
        self.assertIn("plugin/skills/security-review/SKILL.md", files)
        self.assertIn("plugin/commands/new-task.md", files)

    def test_plugin_mode_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "go", "--plugin", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            self.assertFalse((p / ".claude/skills").exists())
            self.assertFalse((p / ".claude/commands").exists())
            self.assertFalse((p / ".claude/agents").exists())
            self.assertTrue((p / ".claude/hooks/protected_paths.py").exists())  # el hook sigue siendo local
            settings = json.loads((p / ".claude/settings.json").read_text())
            self.assertTrue(settings["enabledPlugins"]["aisdlc@aisdlc"])
            self.assertEqual(settings["extraKnownMarketplaces"]["aisdlc"]["source"]["repo"], "franciscogilt/aisdlc")
            self.assertIn("/aisdlc:new-task", (p / "CLAUDE.md").read_text())

    def test_local_mode_keeps_plain_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            sk.main(["--stack", "go", "--out", tmp])
            p = pathlib.Path(tmp)
            self.assertTrue((p / ".claude/skills/security-review/SKILL.md").exists())
            claude_md = (p / "CLAUDE.md").read_text()
            self.assertIn("`/new-task <ID>`", claude_md)
            self.assertNotIn("aisdlc:", claude_md)
            self.assertNotIn("enabledPlugins", (p / ".claude/settings.json").read_text())


class ComposeTests(unittest.TestCase):
    def test_postgres_volume_path_follows_version(self):
        original = sk.RT["postgres"]
        try:
            sk.RT["postgres"] = "17"
            self.assertIn("dbdata:/var/lib/postgresql/data", sk.compose_for("fastapi", "postgres"))
            sk.RT["postgres"] = "18"
            c = sk.compose_for("fastapi", "postgres")
            self.assertIn("dbdata:/var/lib/postgresql\n", c)
            self.assertNotIn("/var/lib/postgresql/data", c)
        finally:
            sk.RT["postgres"] = original


class StarterAppTests(unittest.TestCase):
    def test_with_app_generates_runnable_project_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "fastapi", "--db", "postgres", "--with-app", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            for rel in ("app/main.py", "tests/test_api.py", "requirements.txt", "requirements-dev.txt",
                        "pyproject.toml"):
                self.assertTrue((p / rel).exists(), rel)
            ast.parse((p / "app/main.py").read_text())
            self.assertIn("requirements-dev.txt", (p / ".github/workflows/ci.yml").read_text())
            meta = json.loads((p / ".claude/factory.json").read_text())
            self.assertTrue(meta["with_app"])

    def test_every_starter_app_is_registered_and_in_e2e(self):
        import yaml
        e2e = yaml.safe_load((ROOT / ".github/workflows/e2e.yml").read_text())
        matrix = {m["stack"] for m in e2e["jobs"]["project"]["strategy"]["matrix"]["include"]}
        dirs = {p.name for p in (ROOT / "starter_apps").iterdir() if p.is_dir()}
        self.assertEqual(set(sk.STARTER_APPS), dirs)
        self.assertEqual(set(sk.STARTER_APPS), matrix)

    def test_django_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "django", "--db", "postgres", "--with-app", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            for rel in ("manage.py", "config/settings.py", "core/views.py", "core/tests.py", "requirements.txt"):
                self.assertTrue((p / rel).exists(), rel)
            self.assertIn("APP_ENV: development", (p / ".github/workflows/ci.yml").read_text())
            self.assertIn("config.wsgi", (p / "Dockerfile").read_text())  # el Dockerfile apunta al modulo real
            self.assertIn("gunicorn", (p / "requirements.txt").read_text())

    def test_express_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "express", "--db", "postgres", "--with-app", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            pkg = json.loads((p / "package.json").read_text())
            for script in ("test", "lint"):
                self.assertIn(script, pkg["scripts"])
            self.assertTrue((p / "package-lock.json").exists())  # `npm ci` lo exige
            self.assertNotIn("node_modules", [c.name for c in p.iterdir()])
            self.assertIn("src/index.js", (p / "Dockerfile").read_text())

    def test_dotnet_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "dotnet", "--db", "postgres", "--with-app", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            for rel in ("global.json", "App.slnx", "src/App/Program.cs", "tests/App.Tests/ApiTests.cs"):
                self.assertTrue((p / rel).exists(), rel)
            df = (p / "Dockerfile").read_text()
            self.assertIn("src/App/App.csproj", df)  # publica el proyecto real, no la solucion
            self.assertNotIn("TODO", df)

    def test_springboot_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "springboot", "--db", "postgres", "--with-app", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            for rel in ("pom.xml", "checkstyle.xml", ".mvn/wrapper/maven-wrapper.properties",
                        "src/main/java/com/example/app/App.java"):
                self.assertTrue((p / rel).exists(), rel)
            self.assertTrue(os.access(p / "mvnw", os.X_OK))  # el Dockerfile y el CI ejecutan ./mvnw
            self.assertIn("<java.version>%s</java.version>" % sk.RT["java"], (p / "pom.xml").read_text())

    def test_go_app_has_no_third_party_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "go", "--db", "postgres", "--with-app", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            for rel in ("go.mod", "main.go", "server.go", "server_test.go"):
                self.assertTrue((p / rel).exists(), rel)
            self.assertNotIn("require", (p / "go.mod").read_text())  # politica: solo libreria estandar
            self.assertIn("go %s" % sk.RT["go"], (p / "go.mod").read_text())

    def test_nextjs_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "nextjs", "--db", "postgres", "--with-app", "--out", tmp]), 0)
            p = pathlib.Path(tmp)
            self.assertTrue((p / "package-lock.json").exists())
            self.assertTrue((p / "public").is_dir())  # el Dockerfile copia public/
            self.assertIn("standalone", (p / "next.config.mjs").read_text())

    def test_spa_apps_serve_health_and_copy_the_real_output(self):
        for stack, out in (("react", "/app/dist "), ("angular", "/app/dist/app/browser ")):
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(sk.main(["--stack", stack, "--with-app", "--out", tmp]), 0)
                p = pathlib.Path(tmp)
                self.assertIn(out, (p / "Dockerfile").read_text())
                self.assertNotIn("TODO", (p / "Dockerfile").read_text())
                self.assertIn("/health", (p / "nginx.conf").read_text())
                self.assertTrue((p / "package-lock.json").exists())

    def test_remaining_apps(self):
        cases = {
            "laravel": ("composer.lock", "artisan", "routes/api.php"),
            "rails": ("Gemfile.lock", "bin/rails", "app/controllers/items_controller.rb"),
            "quarkus": ("pom.xml", "mvnw", "src/main/java/com/example/app/ItemResource.java"),
        }
        for stack, files in cases.items():
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(sk.main(["--stack", stack, "--db", "postgres", "--with-app", "--out", tmp]), 0)
                p = pathlib.Path(tmp)
                for rel in files:
                    self.assertTrue((p / rel).exists(), f"{stack}: {rel}")
                for rel in files[1:2]:  # los scripts se ejecutan: necesitan permiso de ejecucion
                    self.assertTrue(os.access(p / rel, os.X_OK), f"{stack}: {rel}")
                self.assertTrue((p / "Dockerfile").exists(), stack)  # Rails sin app no tiene; con app si
                self.assertFalse((p / ".env").exists(), stack)  # nunca se incluyen secretos reales
                self.assertFalse((p / "config/master.key").exists(), stack)

    def test_with_app_unsupported_stack(self):
        original = sk.STARTER_APPS
        sk.STARTER_APPS = ("fastapi",)  # los 12 stacks ya tienen app: simula uno sin ella
        try:
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(sk.main(["--stack", "rails", "--with-app", "--out", tmp]), 2)
        finally:
            sk.STARTER_APPS = original

    def test_generated_python_tooling_is_lint_exempt(self):
        for rel, content, _m, _e in sk.build_files("d", "fastapi", "none", "none", "none", "@o/t"):
            if rel.endswith(".py"):
                self.assertIn("# ruff: noqa", content, rel)




class ExistingProjectTests(unittest.TestCase):
    """Adopcion en un proyecto que ya existe: el kit respeta su gestor de paquetes y su runtime."""

    def gen(self, stack, files):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            for name, content in files.items():
                (p / name).write_text(content)
            self.assertEqual(sk.main(["--stack", stack, "--db", "postgres", "--out", tmp]), 0)
            return {f: (p / f).read_text() for f in (".github/workflows/ci.yml", "Dockerfile")}

    def test_pnpm_project(self):
        out = self.gen("nextjs", {"package.json": '{"scripts": {"build": "next build"}}', "pnpm-lock.yaml": "x"})
        ci = out[".github/workflows/ci.yml"]
        self.assertIn("pnpm install --frozen-lockfile", ci)
        self.assertIn("corepack enable", ci)
        self.assertIn("pnpm run lint --if-present", ci)  # no tiene lint: no debe romper el CI
        self.assertNotIn("npm ci", ci)
        self.assertIn("COPY package.json pnpm-lock.yaml ./", out["Dockerfile"])

    def test_npm_project_with_scripts_is_unchanged(self):
        out = self.gen("nextjs", {"package.json": '{"scripts": {"lint": "x", "test": "x", "build": "x"}}'})
        self.assertIn("npm ci", out[".github/workflows/ci.yml"])
        self.assertNotIn("--if-present", out[".github/workflows/ci.yml"])

    def test_declared_python_runtime_is_respected(self):
        out = self.gen("django", {"runtime.txt": "python-3.10.8\n"})
        self.assertIn('python-version: "3.10"', out[".github/workflows/ci.yml"])
        self.assertIn("FROM python:3.10", out["Dockerfile"])

    def test_malformed_package_json_does_not_crash(self):
        self.gen("express", {"package.json": "{no es json"})


class AdoptModeTests(unittest.TestCase):
    def test_adopt_then_strict_by_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            ci = pathlib.Path(tmp) / ".github/workflows/ci.yml"
            self.assertEqual(sk.main(["--stack", "fastapi", "--adopt", "--out", tmp]), 0)
            self.assertEqual(ci.read_text().count("continue-on-error"), 2)  # lint y auditoria, nada mas
            self.assertEqual(sk.main(["--strict", "lint", "--out", tmp]), 0)
            self.assertEqual(ci.read_text().count("continue-on-error"), 1)
            self.assertIn("adopcion:audit", ci.read_text())
            self.assertEqual(sk.main(["--update", "--out", tmp]), 0)  # update no revierte el modo
            self.assertEqual(ci.read_text().count("continue-on-error"), 1)
            self.assertEqual(sk.main(["--strict", "all", "--out", tmp]), 0)
            self.assertNotIn("continue-on-error", ci.read_text())
            meta = json.loads((pathlib.Path(tmp) / ".claude/factory.json").read_text())
            self.assertFalse(meta["adopt"])

    def test_default_is_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "go", "--out", tmp]), 0)
            self.assertNotIn("continue-on-error", (pathlib.Path(tmp) / ".github/workflows/ci.yml").read_text())


class DeployWorkflowTests(unittest.TestCase):
    def test_every_target_generates_valid_yaml(self):
        import yaml
        combos = [(st, c, "none") for st in ("fastapi", "go") for c in ("aws", "azure", "gcp")]
        combos += [("nextjs", "none", "vercel"), ("react", "none", "netlify")]
        for stack, cloud, deploy in combos:
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(sk.main(["--stack", stack, "--cloud", cloud, "--deploy", deploy, "--out", tmp]), 0)
                data = yaml.safe_load((pathlib.Path(tmp) / ".github/workflows/deploy.yml").read_text())
                self.assertIn("workflow_dispatch", data[True])  # manual: nunca despliega solo
                self.assertEqual(data["jobs"]["deploy"]["environment"], "production")

    def test_no_deploy_workflow_without_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "fastapi", "--out", tmp]), 0)
            self.assertFalse((pathlib.Path(tmp) / ".github/workflows/deploy.yml").exists())


class EvalAndMetricsTests(unittest.TestCase):
    def test_add_eval_appends_case_and_runs_evals(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "go", "--out", tmp]), 0)
            subprocess.run(["git", "init", "-q", tmp], check=True)
            cases = pathlib.Path(tmp) / "evals/hook_cases.json"
            before = len(json.loads(cases.read_text()))
            r = subprocess.run([sys.executable, "scripts/add_eval.py", "borrado de raiz", "--tool", "Bash",
                                "--command", "rm -rf /", "--expect", "block"],
                               cwd=tmp, capture_output=True, text=True)
            self.assertIn("Caso agregado", r.stdout)
            self.assertEqual(len(json.loads(cases.read_text())), before + 1)
            dup = subprocess.run([sys.executable, "scripts/add_eval.py", "borrado de raiz", "--tool", "Bash",
                                  "--command", "x", "--expect", "block"], cwd=tmp, capture_output=True, text=True)
            self.assertNotEqual(dup.returncode, 0)  # no permite nombres repetidos
            self.assertEqual(len(json.loads(cases.read_text())), before + 1)

    def test_metrics_github_flag_is_wired(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sk.main(["--stack", "go", "--out", tmp]), 0)
            src = (pathlib.Path(tmp) / "scripts/metrics.py").read_text()
            ast.parse(src)
            self.assertIn("--github", src)
            self.assertIn("lead_time_h_mediana", src)


if __name__ == "__main__":
    unittest.main()
