---
name: definition-of-done
description: Checklist de "terminado" para una tarea. Usar antes de reportar una tarea como completa o de abrir el PR.
---

# Definition of Done

- [ ] El `plan.md` esta completo; las desviaciones estan anotadas.
- [ ] Tests nuevos cubren el comportamiento nuevo y el caso de error principal.
- [ ] Tests, lint y build pasan (comandos en CLAUDE.md).
- [ ] No hay dependencias nuevas sin justificar.
- [ ] No hay secretos, `console.log`/prints de depuracion ni codigo comentado.
- [ ] Migraciones: generadas con la herramienta del framework y reversibles.
- [ ] La documentacion afectada (README, API, `.env.example`) esta actualizada.
- [ ] El subagente `verifier` devolvio PASS.
- [ ] Revision con la skill `security-review` hecha.
