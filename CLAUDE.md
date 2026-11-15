# proj_springboot

Stack: Spring Boot (Java/Kotlin) | BD: PostgreSQL | Nube: AWS | Deploy: Sin plataforma de deploy

## Comandos (Claude debe correrlos para verificar su propio trabajo)
- Tests: `./mvnw test`
- Lint: `./mvnw checkstyle:check`
- Build: `./mvnw -q -DskipTests package`
- Levantar local: `./mvnw spring-boot:run`
- Servicios locales (BD, etc.): `docker compose up -d`

## Flujo de trabajo (AI-native SDLC)
- Cada tarea vive en `intent/<ID>/` con tres archivos: `intent.md` -> `spec.md` -> `plan.md`.
- Comandos del flujo: `/new-task <ID>`, `/spec <ID>`, `/plan <ID>`, `/build <ID>`, `/verify <ID>`, `/ship <ID>`.
- Antes de editar codigo, lee el `plan.md` de la tarea. Si no existe, detente y pidelo. No inventes alcance.
- Empieza toda tarea no trivial en plan mode.
- Termina cada tarea corriendo tests, lint y build, y corrige los fallos antes de reportar.
- Si te desvias del plan, escribelo bajo `## Desviaciones` en `plan.md` antes de continuar.
- Antes de dar algo por terminado, usa el subagente `verifier` y aplica la skill `definition-of-done`.
- Para revisar seguridad usa la skill `security-review`.

## Reglas del stack
- Las migraciones usan Flyway/Liquibase: archivos nuevos, nunca editar los ya aplicados.
- Inyeccion por constructor; no uses @Autowired en campos.

## Dependencias (politica)
- **No agregues librerias a menos que sea necesario.** Primero usa lo que ya trae el framework o el lenguaje:
  Starters de Spring Boot (Web, Data JPA, Validation, Security, Actuator).
- Antes de agregar una dependencia, comprueba que no exista ya una equivalente en el proyecto y que no se resuelva con ~30 lineas propias.
- Si de verdad hace falta, elige la opcion **mas popular y mas actualizada** de su categoria (skill `new-dependency`):
  1. Mantenimiento activo: release reciente y sin avisos de abandono o deprecacion.
  2. Adopcion amplia: de las mas usadas de su categoria, con comunidad grande.
  3. Compatible con las versiones actuales del framework y del lenguaje del proyecto.
  4. Licencia compatible con uso comercial y sin vulnerabilidades conocidas.
- No elijas de memoria: **verifica la ultima version estable y su mantenimiento** antes de instalar. Como verificar: search.maven.org o `./mvnw versions:display-dependency-updates`; revisa fecha del ultimo release.
- Instala siempre la ultima version estable compatible; nunca fijes una version vieja sin explicar por que.
- Al proponer una dependencia, dilo explicitamente: que problema resuelve, por que no alcanza lo nativo, y por que es la mejor opcion.
- Librerias de referencia para este stack (usalas SOLO si hacen falta): Flyway, Testcontainers, MapStruct (solo si hay mucho mapeo).
- Un hook pide aprobacion humana al editar archivos de dependencias (`pom.xml`, `build.gradle`, `build.gradle.kts`) y al ejecutar comandos que instalan paquetes.

## Datos, nube y deploy
- Base local: `docker compose up -d db`. Nunca apuntes las pruebas a una base remota.
- Toda consulta usa parametros; prohibido concatenar SQL.
- Los cambios de esquema solo van por migraciones.
- Nunca uses credenciales reales de AWS. Solo el perfil de desarrollo/sandbox.
- No ejecutes comandos `aws` que creen, modifiquen o borren recursos sin pedirlo.

## Rutas y comandos protegidos
- Un hook pide aprobacion para editar migraciones, infraestructura, workflows de CI, Docker y `.env`, y bloquea comandos destructivos.
- Las rutas estan en `.claude/protected-paths.json`. No intentes esquivar el hook, ni por Bash.
- Para migraciones e infraestructura, la rama debe incluir un ticket de cambio (ej. `feat/CHG-123-descripcion`).
- Nunca leas ni imprimas el contenido de `.env`.

## Errores conocidos
<!-- Regla: si Claude comete el mismo error dos veces, se agrega aqui. -->
-
