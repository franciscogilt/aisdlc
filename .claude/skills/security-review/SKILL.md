---
name: security-review
description: Revision de seguridad de cambios de codigo. Usar al revisar un PR o antes de dar una tarea por terminada, sobre todo si hay autenticacion, entradas de usuario, SQL, archivos, secretos, red o dependencias nuevas.
---

# Revision de seguridad

Revisa el diff y reporta cada hallazgo con `archivo:linea`, severidad (alta/media/baja) y arreglo propuesto.
No reportes preocupaciones genericas: solo problemas concretos del cambio.

## Checklist
1. **Entradas:** toda entrada externa se valida (tipo, largo, formato) antes de usarse.
2. **Inyeccion:** sin SQL, comandos de shell, rutas de archivo ni plantillas construidas con strings concatenados.
3. **Autenticacion y autorizacion:** cada endpoint nuevo comprueba identidad Y permisos; sin acceso a recursos de otro usuario o tenant (IDOR).
4. **Secretos:** ninguna credencial, token o clave en el codigo, logs, mensajes de error ni tests.
5. **Datos sensibles:** no se registran PII ni secretos en logs; cifrado en transito y en reposo donde corresponda.
6. **Errores:** los mensajes al cliente no filtran trazas ni detalles internos.
7. **Dependencias:** las nuevas cumplen la politica de CLAUDE.md y no tienen vulnerabilidades conocidas.
8. **Infraestructura:** puertos, permisos IAM/roles y CORS lo mas restrictivos posible.

## Salida
Lista ordenada por severidad. Si no hay hallazgos, dilo explicitamente y menciona que revisaste.
