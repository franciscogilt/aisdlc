# Software Factory

Generador de **starter kits AI-native SDLC** para Claude Code. Un comando deja un repositorio listo
para trabajar con Claude de forma controlada: contexto, controles, CI, revisión, evals y métricas.
Basado en el playbook "The AI-native SDLC" de Anthropic.

## Uso

Requiere Python 3.9+ (sin dependencias).

```bash
python3 starterkit.py                                  # interactivo
python3 starterkit.py --stack fastapi --db postgres --cloud aws --with-app \
    --owner @mi-org/plataforma --out ./mi-api          # con app de arranque y tests
python3 starterkit.py --stack go --plugin --out ./mi-go   # skills/comandos desde el plugin compartido
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
| App de arranque (`--with-app`) | app mínima con tests y dependencias fijadas (los **12 stacks**) en `starter_apps/` |

## Plugin compartido

Las skills, el verificador y los comandos también se publican como plugin de Claude Code, para que toda la
organización use la misma versión sin copiarla a cada repo. Se genera desde las mismas plantillas
(`python3 tools/build_plugin.py`; una prueba falla si el plugin queda desactualizado).

```
/plugin install aisdlc --marketplace franciscogilt/aisdlc
```

Con `--plugin`, el proyecto no copia skills/agente/comandos y su `settings.json` habilita el plugin
(los comandos pasan a llamarse `/aisdlc:new-task`, etc.). **El hook sigue siendo local** al proyecto: así
funciona aunque el plugin no esté instalado y se puede probar en el CI del proyecto.

## Mantenimiento automático

- `tools/update_versions.py` consulta endoflife.date (runtimes: último ciclo no-EOL con ≥ 60 días; LTS en Node/Java/.NET),
  los releases de las GitHub Actions y PyPI (dependencias de las apps de arranque). El workflow
  `update-versions.yml` lo ejecuta cada semana y abre un PR.
- `E2E` (workflow): solo prueba los stacks afectados en un PR (`tools/e2e_plan.py`); en `main`, manual o si cambia el generador, corre los 12. Por cada app de arranque genera un proyecto, ejecuta los pasos del `ci.yml` generado,
  los evals del hook, lint del Dockerfile (hadolint), `docker build` y `docker compose up` con prueba de `/health`.
- `tools/run_ci_locally.py PROYECTO --venv DIR` ejecuta en tu máquina los comandos del `ci.yml` generado.

## Proyecto que ya existe

El kit se puede aplicar sobre un repositorio con código (no pisa nada: lo que ya existe se omite o queda como `*.starter.*`).
Al hacerlo adapta lo que detecta y lo avisa al terminar:
- **Node:** usa pnpm o yarn si hay `pnpm-lock.yaml` / `yarn.lock` (CI y Dockerfile con corepack); si falta el script `lint`, `test` o `build`, el CI lo omite (`--if-present`) en vez de fallar.
- **Runtime:** respeta la versión declarada en `runtime.txt`, `.python-version`, `.nvmrc` o `.ruby-version` en lugar de imponer la de la fábrica.

Probado sobre dos repos reales (un Next.js con pnpm y un Django de 2022): el CI ya no falla por suposiciones del kit y, en cambio, marca lo que de verdad hay que arreglar (lint, vulnerabilidades, tests ausentes).

### Adopción gradual

En un repo con deuda, `--adopt` deja lint y auditoría de dependencias como avisos (`continue-on-error`) para que el CI no nazca en rojo.
Cuando limpies cada uno: `--strict lint`, `--strict audit` o `--strict all`. `--update` conserva el modo.

## Base de datos y despliegue

- Todas las apps de backend (FastAPI, Django, Express, Spring Boot, Quarkus, .NET, Go, Rails y Laravel) con `--with-app --db postgres` traen repositorio con memoria o Postgres (según `DATABASE_URL`),
  migraciones SQL con bloqueo y `GET/POST /items`; los tests corren contra ambos backends y el E2E crea y lee un ítem en compose.
  Laravel es la excepción idiomática: Eloquent con migraciones de Laravel y SQLite cuando no hay `DATABASE_URL`.
- `--cloud aws|azure|gcp` o `--deploy vercel|netlify` generan `.github/workflows/deploy.yml`: solo manual (`workflow_dispatch`),
  con `environment: production` (protégelo con revisores) y OIDC en las nubes. Configura secretos y variables antes de usarlo.

## Medir y aprender de fallos

- `python3 scripts/metrics.py` mide ciclo, commits y desviaciones del plan por tarea; con `--github OWNER/REPO` añade lead time de PRs,
  tasa de rechazo, CI en verde y comentarios de bot vs humanos (necesita `gh`).
- `python3 scripts/add_eval.py "descripcion" --tool Bash --command "..." --expect block` convierte un fallo real del agente en un caso de eval y corre los evals.

## Cómo lo usa un equipo

1. `intent.md` → `spec.md` → `plan.md` por tarea, en `intent/<ID>/`; cada artefacto se commitea.
2. Construcción con feedback loop (tests/lint/build), verificador independiente y PR.
3. Controles automáticos: hook, permisos, CI, Claude en modo observación, code owners, rama protegida.
4. Mejora continua: cada error repetido va a "Errores conocidos"; cada política compartida, a una skill;
   cada fallo real del agente, a un caso de eval.

## Qué está verificado y qué no

**Verificado en este entorno:**
- 51 pruebas unitarias (`python3 -m unittest discover -s tests`): los 12 stacks (render, JSON/YAML válidos, hook),
  `--update`, `--with-app`, `--plugin`, métricas y la lógica de actualización de versiones (con datos de prueba).
- Hook probado en **sesiones reales de Claude Code 2.1.325**: bloquea migraciones sin ticket, bloquea el bypass por Bash y pide aprobación para instalar paquetes.
- Los workflows de los 12 stacks pasan `actionlint`; los 12 `docker-compose.yml` pasan `docker compose config`.
- **Los 12 stacks de punta a punta:** el kit con `--with-app` pasa todos los pasos de su
  `ci.yml` (instalar, lint, tests, build, auditoría de dependencias). FastAPI, Django y Express los probé también en mi entorno.
  Estas pruebas detectaron y corrigieron fallos reales: el lint marcaba como errores los scripts generados, y el CI de Django necesitaba `APP_ENV`.
- Plugin: `claude plugin validate` pasa; se instaló desde un marketplace local y Claude Code listó 9 skills/comandos y 1 agente.
- Las versiones de la app de arranque se fijaron consultando PyPI en vivo.

**Se verifica en GitHub Actions (workflows `Tests` y `E2E`), no en mi entorno:**
- Las 12 apps de arranque, incluyendo `docker build`, `docker compose up` y el lint del Dockerfile.  Solo FastAPI, Django y Express los probé además en mi entorno; el resto solo en Actions (no hay dotnet ni acceso a Maven Central, NuGet, Packagist ni RubyGems desde mi entorno).
- La consulta a endoflife.date y a los releases de Actions (`update-versions.yml`): desde mi entorno esas dos fuentes no eran accesibles.

**No verificado (hazlo en tu primer proyecto):**
- Las apps de arranque son mínimas (salud + un endpoint con validación): comprueban que el kit funciona, no son una arquitectura de referencia.
- `--plugin` en un proyecto real: las claves `extraKnownMarketplaces` y `enabledPlugins` siguen el formato documentado, pero no probé una sesión con un marketplace de GitHub privado.
- `claude-code-action` y `scripts/protect-main.sh` requieren tu secreto y permisos de admin.
- Los comandos de test/lint/build de los demás stacks son los típicos; confirma que coinciden con tu proyecto.
- El hook de Bash es heurístico, no un sandbox. La auditoría de Java genera un SBOM con CycloneDX y lo escanea con OSV-Scanner (incluye dependencias transitivas; verificado en Actions con Spring Boot y Quarkus).
- Rails: el kit no genera Dockerfile porque Rails 8 trae el suyo.

## Desarrollo

```bash
pip install pyyaml
python3 -m unittest discover -s tests -v
```
- Añadir un stack: una entrada en `STACKS`, `DEPS` y `_PIPE` de `starterkit.py`; las pruebas fallan si falta alguna.
- Añadir una app de arranque: carpeta `starter_apps/<stack>/` con requisitos fijados, agrega el stack a `STARTER_APPS` y a la matriz de `e2e.yml`.
- Cambiar skills, verificador o comandos: edita las plantillas en `starterkit.py` y ejecuta `python3 tools/build_plugin.py`.
