# Software Factory

Generador de **starter kits AI-native SDLC** para Claude Code. Un comando deja un repositorio listo
para trabajar con Claude de forma controlada: contexto, controles, CI, revisión, evals y métricas.
Basado en el playbook "The AI-native SDLC" de Anthropic.

## Uso

Requiere Python 3.9+ (sin dependencias).

```bash
python3 starterkit.py                                  # interactivo
python3 starterkit.py --stack go --db postgres --cloud aws --deploy none \
    --owner @mi-org/plataforma --out ./mi-api
python3 starterkit.py --update --out ./mi-api          # actualiza archivos gestionados
python3 starterkit.py --list
```

**Stacks (12):** fastapi, django, dotnet, springboot, quarkus, laravel, go, rails, express, nextjs, react, angular.
**BD:** postgres, dynamodb. **Nube:** aws, azure, gcp. **Deploy:** vercel, netlify.

Después abre `SDLC-README.md` en el proyecto generado y sigue su sección *Configuración única*.

## Qué genera

| Área | Archivos |
|---|---|
| Contexto del agente | `CLAUDE.md` (comandos, reglas del stack, **política de dependencias**), `.claude/protected-paths.json` |
| Controles | hook `PreToolUse` que **falla cerrado** (archivos + Bash), `.claude/settings.json` con deny/ask |
| Flujo | slash commands `/new-task /spec /plan /build /verify /ship`, plantillas `intent/_templates/` |
| Calidad | subagente `verifier`, skills `security-review`, `new-dependency`, `definition-of-done` |
| CI/CD | `ci.yml` (lint, test, build, auditoría de dependencias, secretos, CodeQL), `dependabot.yml` |
| Revisión | `claude-review.yml` (modo observación), `claude.yml` (`@claude`), `CODEOWNERS`, plantilla de PR, `scripts/protect-main.sh` |
| Runtime | `Dockerfile`, `docker-compose.yml`, `.env.example`, `.dockerignore` |
| Evals y métricas | `evals/run_hook_evals.py` (determinista, corre en CI), `evals/run_behavior_evals.py` (experimental), `scripts/metrics.py` |

## Cómo lo usa un equipo

1. `intent.md` → `spec.md` → `plan.md` por tarea, en `intent/<ID>/`; cada artefacto se commitea.
2. Construcción con feedback loop (tests/lint/build), verificador independiente y PR.
3. Controles automáticos: hook, permisos, CI, Claude en modo observación, code owners, rama protegida.
4. Mejora continua: cada error repetido va a "Errores conocidos"; cada política compartida, a una skill;
   cada fallo real del agente, a un caso de eval.

## Qué está verificado y qué no

**Verificado (en este entorno):**
- 10 pruebas unitarias (`python3 -m unittest discover -s tests`) sobre los 12 stacks: render, JSON/YAML válidos, hook, `--update`, métricas.
- Hook probado en **sesiones reales de Claude Code 2.1.325**: bloquea migraciones sin ticket, bloquea el bypass por Bash y pide aprobación para instalar paquetes; el comando permitido se ejecuta.
- Los workflows de los 12 stacks pasan `actionlint`; los 12 `docker-compose.yml` pasan `docker compose config`.
- `run_behavior_evals.py` corrió 3/3 contra Claude real.

**No verificado (hazlo en tu primer proyecto):**
- Los **Dockerfiles no se construyeron** (no había daemon de Docker). Tienen `TODO` que ajustar (comando de arranque, carpeta de salida).
- Los **workflows no se ejecutaron en GitHub**; `claude-code-action` y `scripts/protect-main.sh` requieren tu secreto/permisos de admin.
- Los comandos de test/lint/build de cada stack son los típicos; confirma que coinciden con tu proyecto.
- Versiones de runtime y de Actions (`RT` en `starterkit.py`) salen de conocimiento hasta junio 2026: actualízalas; Dependabot las mantiene después.
- El hook de Bash es heurístico, no un sandbox. Las auditorías de dependencias no cubren Java (usa Dependabot alerts u OWASP dependency-check).
- Rails: el kit no genera Dockerfile porque Rails 8 trae el suyo.

## Desarrollo

```bash
python3 -m unittest discover -s tests -v
```
Para añadir un stack: una entrada en `STACKS`, `DEPS` y `_PIPE` de `starterkit.py`; las pruebas fallan si falta alguna.
