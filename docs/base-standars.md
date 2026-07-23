---
description: Este documento contiene todas las reglas y lineamientos de desarrollo del proyecto, aplicables a Claude Code.
alwaysApply: true
---

## 1. Principios Fundamentales

- **Tareas pequeñas, una a la vez**: Trabajar siempre en pasos cortos ("baby steps"), uno a la vez. Nunca avanzar más de un paso.
- **Test-Driven Development**: Empezar con tests que fallen para cualquier funcionalidad nueva (TDD), según el detalle de la tarea.
- **Type Safety**: Todo el código debe estar completamente tipado.
- **Nombres claros**: Usar nombres claros y descriptivos para todas las variables y funciones.
- **Cambios incrementales**: Preferir cambios incrementales y focalizados por encima de modificaciones grandes y complejas.
- **Cuestionar supuestos**: Cuestionar siempre los supuestos e inferencias.
- **Detección de patrones**: Detectar y señalar patrones de código repetidos.

## 2. Estándares de Idioma

- **Solo inglés en artefactos de código**: Todo lo que forma parte del código o se ejecuta/parsea debe usar siempre inglés, incluyendo:
    - Código (variables, funciones, clases, comentarios, mensajes de error, mensajes de log)
    - Esquemas de datos y nombres de bases de datos
    - Archivos de configuración y scripts
    - Mensajes de commit de Git
    - Nombres y descripciones de tests
- **Español permitido en documentación de proceso**: Documentos como este (`base-standards.md`), `README.md`, guías internas, docs de API pensadas para el equipo, y work items de Azure DevOps (títulos, descripciones, comentarios) pueden redactarse en español técnico. Lo importante es no mezclar idiomas dentro de un mismo artefacto de código, y mantener consistencia dentro de cada documento.

## 3. Estándares Específicos

Para estándares y lineamientos detallados específicos de cada área del proyecto, consultar:

- [Estándares de Backend](./backend-standards.md) - Desarrollo de API, patrones de base de datos, testing, seguridad y mejores prácticas de backend
- [Estándares de Frontend](./frontend-standards.md) - Componentes de React, lineamientos de UI/UX y arquitectura de frontend
- [Estándares de Documentación](./documentation-standards.md) - Estructura, formato y mantenimiento de documentación técnica, incluyendo estándares de IA como este documento
- [Pasos Obligatorios de Tareas OpenSpec](./openspec-tasks-mandatory-steps.md) - Checklist requerido y reglas de ejecución al crear o actualizar archivos `tasks.md` de OpenSpec

## 4. Skills del Proyecto

- Los skills viven en `.claude/skills`.
- Cuando una solicitud coincida con un skill, cargar y seguir el `SKILL.md` correspondiente automáticamente antes de continuar.
- Cargar también cualquier archivo referenciado dentro de la carpeta del skill (por ejemplo, `references/*.md`) cuando el skill lo requiera.

## 5. Requisito de Modelo para Planificación

Los flujos de planificación deben ejecutarse con Opus en razonamiento alto ("high reasoning").

Este requisito aplica a:
- `enrich-us`
- `openspec-ff-change`
- `openspec-continue-change`

Antes de iniciar cualquiera de estos flujos, verificar que la sesión esté usando Opus en razonamiento alto. Si no lo está, **autocorregirse** agregando `"model": "claude-opus-4-7"` en `.claude/settings.json` (usando el skill `update-config` o editando directamente), y luego continuar — no detenerse a preguntarle al usuario. Hacer lo mismo para volver a sonnet en razonamiento medio en cualquier otro paso.

## 6. Actualizaciones Obligatorias de Artefactos OpenSpec para Cambios Posteriores a Apply

Cuando aparezca una solicitud de fix/cambio nuevo después de `opsx:apply` (o `/apply`) y antes de `opsx:archive` (o `/archive`), los agentes deben tratarla primero como una actualización de spec, no como un "arreglemos esto rápido" informal. Es el principio central de OpenSpec: la documentación es la fuente de verdad.

Orden requerido:

1. Actualizar los artefactos del cambio OpenSpec actual que se vean afectados (por ejemplo: escenarios, requerimientos/specs y `tasks.md`). No agregar tareas como "bugfixes" sueltos, sino como parte del diseño inicial, en la sección correspondiente.
2. Si se necesita regenerar artefactos, correr el paso de OpenSpec correspondiente (`opsx:continue`, `opsx:ff`, o equivalente) antes de codificar.
3. Implementar código solo después de que los artefactos reflejen la nueva solicitud.
4. Volver a correr la verificación contra los artefactos actualizados antes de archivar.

No aplicar fixes de solo código en esta ventana sin antes actualizar los artefactos de OpenSpec.