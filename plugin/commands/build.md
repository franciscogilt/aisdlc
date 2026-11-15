---
description: Implementa plan.md con feedback loop
argument-hint: <ID>
---

Implementa `intent/$ARGUMENTS/plan.md` paso a paso. Tras cada paso corre tests y lint (CLAUDE.md) y corrige los fallos antes de seguir. Si algo no cabe en el plan, anotalo en `## Desviaciones`. Respeta la politica de dependencias. Al final corre tests, lint y build completos.
