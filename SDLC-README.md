# Guia de la fabrica: AI-native SDLC con Claude Code

Stack: FastAPI (Python) · generado con starterkit 1.0.0

## Modelo de trabajo
Cada tarea es un ciclo corto. Cada etapa deja UN archivo en Git y la siguiente empieza leyendolo.
Las personas fijan la intencion y aprueban en las puertas; Claude hace el trabajo entre ellas.

| Etapa | Comando | Artefacto | Puerta humana |
|---|---|---|---|
| Intencion | `/new-task <ID>` | `intent/<ID>/intent.md` | El PO lo corrige y lo marca `aceptado` |
| Diseno | `/spec <ID>` | `intent/<ID>/spec.md` | El PO / tech lead lo revisa |
| Plan | `/plan <ID>` (plan mode) | `intent/<ID>/plan.md` | Un ingeniero lo aprueba |
| Construccion | `/build <ID>` | codigo + tests | Hooks y permisos vigilan mientras tanto |
| Verificacion | `/verify <ID>` | veredicto PASS/FAIL | El verificador es independiente |
| Entrega | `/ship <ID>` | PR | Review humano + CI + code owners |

Regla de oro: las decisiones viven en `intent/`, `spec.md` y `plan.md`, no en chats ni DMs.

## Configuracion unica (una vez por repositorio)
1. Revisa `CLAUDE.md`: comandos de test/lint/build reales de tu proyecto, y completa "Errores conocidos".
2. Ajusta los `TODO` de `Dockerfile` (comando de arranque, carpeta de salida).
3. Reemplaza el equipo en `.github/CODEOWNERS`.
4. En GitHub: agrega el secreto `ANTHROPIC_API_KEY` y activa Dependabot alerts y secret scanning.
5. Protege `main`:  `./scripts/protect-main.sh OWNER/REPO`  (necesita `gh` con permisos de admin).
6. Verifica la configuracion del agente:  `python3 evals/run_hook_evals.py`
7. Primer PR: confirma que el job `quality` corre en verde. Si el proyecto no tiene tests, pide:
   "Agrega pruebas basicas y dime como correrlas". Sin tests no hay feedback loop.

## Controles que ya tienes
- **Hook** (`.claude/hooks/protected_paths.py`): migraciones, infraestructura, CI, Docker y `.env` exigen ticket
  `CHG-####` en la rama y aprobacion humana; bloquea comandos destructivos; pide aprobacion al instalar paquetes.
  Falla cerrado. Es heuristico en Bash: no sustituye la proteccion de ramas.
- **Permisos** (`.claude/settings.json`): deny/ask para push, terraform, instalaciones y lectura de `.env`.
- **CI** (`ci.yml`): lint, test, build, auditoria de dependencias, secretos en el historial y CodeQL (si aplica).
- **Revision** (`claude-review.yml`): Claude comenta cada PR en modo observacion. Cuando sus hallazgos sean
  fiables, convierte el job en check obligatorio. Muestrea PRs aprobados por Claude y revisalos a mano.
- **Evals** (`evals/`): `run_hook_evals.py` corre en CI cuando cambia `.claude/`, `CLAUDE.md` o `evals/`.
  `run_behavior_evals.py` es experimental. Agrega un caso cada vez que Claude cometa un error real.
- **Metricas**: `python3 scripts/metrics.py` (ciclo por tarea, commits, desviaciones del plan).

## Mantener la fabrica
- Mejoras del kit: `python3 starterkit.py --update --out .` actualiza solo los archivos gestionados
  (hook, runners de evals, skills, comandos, verificador, workflows de Claude, metricas). Tus archivos
  (`CLAUDE.md`, `ci.yml`, Dockerfile...) no se tocan; si cambian las plantillas base veras `*.starter.*`.
  Para personalizar una skill, copiala con otro nombre en vez de editar la original.
- Si Claude repite un error: agregalo a "Errores conocidos". Si es una politica de varios repos: skill.
- Si usas `claude -p --bare` en CI: `--bare` omite hooks, skills y CLAUDE.md; pasa los hooks con `--settings`.
