---
description: Estándares y mejores prácticas para la documentación técnica de este proyecto, incluyendo estructura de documentación, procesos de actualización y reglas de idioma.
globs:
alwaysApply: true
---
# Reglas y Patrones para Documentación y AI Specs

## Introducción

La documentación técnica abarca toda la documentación relativa al proyecto, como el modelo de datos, el README, las specs de API, y otros documentos `.md` que describen cómo está estructurado, cómo corre y cómo opera el proyecto.

Los AI specs se refieren a los documentos que le explican a los agentes de IA cómo comportarse, documentar, planificar, codificar, etc., lo cual incluye acuerdos de equipo, estándares y convenciones (como este mismo documento, `base-standards.md`, `backend-standards.md`, `frontend-standards.md` y `openspec-tasks-mandatory-steps.md`).

## Reglas Generales de Idioma

- **Código y artefactos técnicos → siempre en inglés**: variables, funciones, clases, comentarios dentro del código, mensajes de error, mensajes de log, esquemas de datos, nombres de bases de datos, archivos de configuración, scripts, mensajes de commit, nombres y descripciones de tests.
- **Documentación de proceso → español técnico permitido**: este documento, `README.md`, guías internas, AI specs, y work items de Azure DevOps pueden redactarse en español técnico. Lo que importa es no mezclar idiomas dentro de un mismo artefacto y mantener consistencia dentro de cada documento.
- Esta regla es la misma definida en la Sección 2 de `base-standards.md` — si hay alguna discrepancia entre ambos documentos, `base-standards.md` es la fuente de verdad.

## Documentación Técnica

Antes de hacer cualquier commit o git push, o si se te pide documentar un commit, siempre debés revisar qué documentación técnica debería actualizarse.

Al actualizar documentación, se debe:

1. Revisar todos los cambios recientes en el código
2. Identificar qué archivos de documentación necesitan actualizarse según los cambios. Algunos ejemplos claros:
   - Para cambios en el modelo de datos: actualizar la sección de definición del modelo de datos en `data-model.md`
   - Para cambios en la API: actualizar `api-spec.yml`
   - Para cambios en librerías, migraciones de base de datos, o cualquier cosa que modifique el proceso de instalación: actualizar `*-standards.md`
3. Actualizar cada archivo de documentación afectado (en español técnico si es documentación de proceso, en inglés si es código o artefacto técnico), manteniendo consistencia con la documentación existente
4. Asegurar que toda la documentación esté correctamente formateada y siga la estructura establecida
5. Verificar que todos los cambios queden reflejados con precisión en la documentación
6. Reportar qué archivos se actualizaron y qué cambios se hicieron

## AI Specs

Esta regla establece un proceso obligatorio para que la IA:

- Aprenda del feedback, las indicaciones y las sugerencias del usuario durante las interacciones.
- Identifique proactivamente oportunidades para mejorar las Reglas de Desarrollo existentes basándose en estos aprendizajes.
- Mantenga la asistencia de la IA alineada con las necesidades evolutivas del proyecto y las expectativas del usuario.
- Incorpore el feedback del usuario al marco operativo de la IA para maximizar su valor.

Esta regla aplica después de cualquier interacción donde el usuario dé feedback explícito o implícito, sugerencias, correcciones, información nueva, o exprese preferencias. **La IA DEBE analizar activamente todas las interacciones del usuario en busca de este tipo de oportunidades de aprendizaje, no limitarse a esperar pasivamente un feedback directo, para refinar proactivamente su entendimiento y las mejores prácticas del proyecto.**

### Errores Comunes y Anti-Patrones que la IA Debe Evitar

- **Saltarse el proceso de aprobación**: Aplicar modificaciones a las reglas sin obtener primero revisión y aprobación explícita del usuario.
- **Propuestas sin vínculo claro**: Proponer cambios a las reglas sin conectarlos claramente con el feedback específico del usuario o los aprendizajes obtenidos de la interacción.
- **Modificaciones imprecisas**: Sugerir modificaciones sin identificar con precisión qué regla o qué secciones específicas dentro de una regla deberían cambiarse, dificultando la revisión efectiva por parte del usuario.
- **Feedback no atendido**: No iniciar el proceso de aprendizaje y revisión cuando el usuario da feedback relevante que podría mejorar las reglas.
- **Scope creep**: Actualizar múltiples reglas no relacionadas simultáneamente, o hacer cambios que excedan el alcance del feedback recibido.
- **Cambios de reglas no solicitados**: Modificar reglas proactivamente cuando no hay una conexión directa con feedback del usuario o una oportunidad de aprendizaje real. Las actualizaciones de reglas deben ser reactivas y estar impulsadas por el feedback recibido.
- **Confirmación de actualización faltante**: No notificar al usuario después de que una modificación de regla se haya implementado exitosamente tras su aprobación.