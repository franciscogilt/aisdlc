---
name: new-dependency
description: Decidir si agregar una libreria y cual elegir. Usar siempre antes de instalar o declarar una dependencia nueva en cualquier archivo de manifiesto.
---

# Agregar una dependencia

1. **Necesidad:** explica que problema resuelve. Intenta resolverlo con lo nativo del framework o del lenguaje, o con unas 30 lineas propias. Si alcanza, no agregues nada.
2. **Candidatas:** identifica las 2-3 opciones mas usadas de su categoria.
3. **Verificacion (no de memoria):** comprueba con el comando del ecosistema (ver CLAUDE.md) o buscando en la web:
   - ultima version estable y fecha del ultimo release (rechaza abandono: sin releases en ~12 meses);
   - adopcion (descargas, estrellas, uso en proyectos grandes);
   - compatibilidad con las versiones de framework/lenguaje de este proyecto;
   - licencia compatible con uso comercial; sin vulnerabilidades conocidas;
   - tamano y numero de dependencias transitivas.
4. **Propuesta:** presenta a la persona una tabla corta (opcion, version, ultimo release, adopcion, licencia) con tu recomendacion y por que.
5. **Instala** solo tras su aprobacion, siempre la ultima version estable compatible.
