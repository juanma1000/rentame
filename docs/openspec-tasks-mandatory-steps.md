---
description: Aplica los pasos obligatorios de openspec/config.yaml al crear artefactos tasks.md y asegura que el agente ejecute todos los tests manuales
alwaysApply: true
---

# OpenSpec Tasks: Enforcement de Pasos Obligatorios

Al crear o actualizar artefactos `tasks.md` en los cambios de OpenSpec, DEBÉS:

## 1. Leer openspec/config.yaml Primero

**ANTES** de crear o actualizar cualquier archivo `tasks.md`, DEBÉS leer `openspec/config.yaml` para entender:
- Los pasos obligatorios específicos de backend y frontend
- Las convenciones de nomenclatura de branches
- Los requisitos de estructura de tareas
- Los requisitos de testing y documentación
- **A qué subagente se delega cada fase** (`backend-expert`, `frontend-expert`, `qa-expert`) según las reglas `apply`/`verify` definidas en `config.yaml` — este documento define QUÉ pasos son obligatorios; `config.yaml` define QUIÉN los ejecuta

## 2. Pasos Obligatorios

Toda tarea de implementación DEBE incluir estos pasos en el orden correcto:

### Paso 0: Crear Feature Branch (DEBE SER EL PRIMERO)
- **Ubicación**: Debe ser el primer paso (Paso 0)
- **Nomenclatura de branch**: `feature/[change-name]-backend` para cambios de backend, `feature/[change-name]-<nombre-del-microfrontend>` para cambios de frontend (ej. `feature/update-position-candidates-app`)
- **Acción**: Crear y cambiar al feature branch antes de cualquier cambio de código

### Pasos Obligatorios (Deben Incluirse):
- **Paso N**: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)
- **Paso N+1**: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)
- **Paso N+2**: Testing Manual de Endpoints con curl (OBLIGATORIO) - **EL AGENTE DEBE EJECUTARLO**
- **Paso N+3**: Testing E2E con Playwright MCP (OBLIGATORIO si aplica) - **EL AGENTE DEBE EJECUTARLO**
- **Paso N+4**: Actualizar Documentación Técnica (OBLIGATORIO)

## 3. Requisitos de Testing Manual - CRÍTICO: El Agente Debe Ejecutarlo

**IMPORTANTE**: El agente de código (IA) DEBE realizar todos los pasos de testing manual él mismo. **NUNCA delegar el testing al usuario**. Estos tests deben ser ejecutados por el agente para poder marcar las tareas como completadas en `tasks.md`.

### Paso N+1: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

**Responsabilidad del agente**: El agente de código DEBE ejecutar los unit tests, validar la integridad de la base de datos antes/después de la ejecución, y producir un artefacto de reporte de test en la carpeta de specs del cambio. Esto NO es opcional y no puede delegarse al usuario.

**Pasos de Implementación** (el agente debe realizarlos):
1. **Preparar el Entorno de Test**:
   - Asegurar que los servicios requeridos estén disponibles (base de datos, cache, dependencias)
   - Capturar el estado de la base de datos previo al test, relevante para el cambio (conteos, registros clave, checksums, o snapshots)
   - Documentar el/los comando(s) exacto(s) de test que se van a ejecutar

2. **Correr Primero los Unit Tests Focalizados**:
   - Ejecutar tests focalizados para el/los módulo(s) modificado(s) y comportamiento relacionado
   - Confirmar que las fallas se resolvieron y que no aparecen nuevas regresiones en el scope focalizado
   - Capturar el resumen del output del comando (passed/failed/skipped)

3. **Correr la Suite de Unit Tests Más Amplia**:
   - Ejecutar la suite de tests del proyecto requerida por `openspec/config.yaml` (o el subconjunto justificado si está configurado así)
   - Registrar el total de tests, fallas, tiempo de ejecución, y cualquier comportamiento flaky observado

4. **Verificar el Estado de la Base de Datos Post-Test**:
   - Volver a chequear los mismos indicadores de base de datos capturados antes de los tests
   - Confirmar que no queden mutaciones no intencionadas después de que los tests terminen
   - Si ocurrió alguna mutación, restaurar el estado y documentar la restauración

5. **Crear el Reporte de Verificación de Unit Tests en la Carpeta de Specs**:
   - Guardar el reporte dentro de la carpeta del cambio actual, en `specs/<change-name>/reports/`
   - Usar este patrón de nombre de archivo: `YYYY-MM-DD-step-N+1-unit-test-and-db-verification.md`
   - Incluir los comandos ejecutados, resultados resumidos, comparación pre/post de la base de datos, y acciones de limpieza

6. **Marcar la Tarea como Completada**: Solo después de que los unit tests pasen (o las excepciones aprobadas estén documentadas), el estado de la base de datos esté verificado/restaurado, y el archivo de reporte esté creado, marcar el Paso N+1 como completado en `tasks.md`.

**Plantilla de Reporte** (guardar en `specs/<change-name>/reports/`):
```markdown
# Reporte Paso N+1 - Unit Tests y Verificación de Base de Datos

- Fecha: YYYY-MM-DD
- Cambio: <change-name>
- Agente: <nombre-del-agente>

## Comandos Ejecutados
- `<comando 1>`
- `<comando 2>`

## Resultados de Unit Tests
- Tests focalizados: X passed, Y failed, Z skipped
- Suite completa/requerida: X passed, Y failed, Z skipped
- Duración: <duración>
- Notas: <tests flaky, reintentos, excepciones>

## Verificación de Estado de Base de Datos
- Baseline pre-test:
  - <métrica/tabla/check>: <valor>
- Validación post-test:
  - <métrica/tabla/check>: <valor>
- Estado restaurado: Sí/No
- Acciones de restauración (si aplica): <acciones>

## Resultado
- Estado del Paso N+1: PASS/FAIL
- Issues bloqueantes: <ninguno o lista>
```

**Dependencias**:
- Test runner y dependencias de test del proyecto instaladas
- Acceso a la base de datos para verificación/restauración de estado
- Permiso para crear archivos de reporte en `specs/<change-name>/reports/`

**Notas**:
- **El agente DEBE ejecutar los tests él mismo** — nunca pedirle al usuario que corra los tests
- Este paso es obligatorio incluso cuando los cambios de código parezcan pequeños
- El nombre del reporte debe seguir el patrón requerido para trazabilidad
- **La tarea en tasks.md solo puede marcarse como completada después de crear el reporte**

### Paso N+2: Testing Manual de Endpoints con curl (OBLIGATORIO)

**Responsabilidad del agente**: El agente de código DEBE ejecutar todos los comandos curl y verificar las respuestas. Esto NO es opcional y no puede delegarse al usuario.

**Pasos de Implementación** (el agente debe realizarlos):
1. **Preparar el Entorno de Test**:
   - Asegurar que el servidor backend esté corriendo (iniciarlo si hace falta — ej. `uvicorn app.main:app`)
   - Verificar que la conexión a la base de datos esté activa
   - Anotar el estado actual de la base de datos (si se están testeando endpoints CREATE/UPDATE/DELETE)

2. **Testear Endpoints GET** (si aplica):
   - Crear el comando curl para testear el endpoint GET
   - Ejecutar el comando curl: `curl -X GET [endpoint-url] [headers]`
   - Verificar el código de estado de la respuesta (200, 404, etc.)
   - Verificar la estructura y contenido del body de la respuesta
   - Documentar el comando curl y la respuesta en el reporte de la tarea

3. **Testear Endpoints POST** (operaciones CREATE):
   - Crear el comando curl con el body del request: `curl -X POST [endpoint-url] -H "Content-Type: application/json" -d '[json-body]'`
   - Ejecutar el comando curl y capturar la respuesta
   - Verificar el código de estado de la respuesta (201, 400, 422, etc. — FastAPI devuelve 422 para errores de validación de Pydantic)
   - Verificar que el body de la respuesta contenga el recurso creado
   - **Restaurar el Estado de la Base de Datos**: después de testear, eliminar el registro creado para restaurar la base de datos a su estado original
   - Documentar el comando curl, la respuesta, y la acción de limpieza

4. **Testear Endpoints PUT/PATCH** (operaciones UPDATE):
   - Crear el comando curl con los datos actualizados: `curl -X PUT [endpoint-url] -H "Content-Type: application/json" -d '[json-body]'`
   - Ejecutar el comando curl y capturar la respuesta
   - Verificar el código de estado de la respuesta (200, 404, 400, etc.)
   - Verificar que el body de la respuesta contenga el recurso actualizado
   - **Restaurar el Estado de la Base de Datos**: después de testear, revertir el registro actualizado a sus valores originales
   - Documentar el comando curl, la respuesta, y la acción de limpieza

5. **Testear Endpoints DELETE**:
   - Crear el comando curl: `curl -X DELETE [endpoint-url]`
   - Ejecutar el comando curl y capturar la respuesta
   - Verificar el código de estado de la respuesta (200, 204, 404, etc.)
   - Verificar que la eliminación fue exitosa
   - **Restaurar el Estado de la Base de Datos**: después de testear, recrear el registro eliminado con sus valores originales
   - Documentar el comando curl, la respuesta, y la acción de limpieza

6. **Testear Casos de Error**:
   - Testear con datos inválidos (errores de validación)
   - Testear con recursos inexistentes (errores 404)
   - Testear con acceso no autorizado (si aplica)
   - Verificar que el formato de la respuesta de error coincida con la especificación de la API

7. **Marcar la Tarea como Completada**: Solo después de que todos los tests de curl pasen y el estado de la base de datos esté restaurado, marcar la tarea como completada en `tasks.md`

**Dependencias**:
- Servidor backend corriendo (el agente debe iniciarlo si hace falta)
- Acceso a la base de datos para restauración de estado
- Herramienta de línea de comandos curl

**Notas**:
- Este paso es OBLIGATORIO para todos los endpoints nuevos
- **El agente DEBE ejecutar todos los comandos curl él mismo** — nunca pedirle al usuario que corra los tests
- Todas las operaciones CREATE/UPDATE/DELETE deben restaurar la base de datos a su estado original después del testing
- Documentar todos los comandos curl y respuestas para referencia futura, en un reporte dentro de la carpeta de specs con el nombre apropiado
- Verificar que el estado de la base de datos coincida con el estado pre-test después de la limpieza
- No saltarse el testing manual incluso si los unit tests pasan
- **La tarea en tasks.md solo puede marcarse como completada después de la ejecución exitosa de todos los tests de curl**

### Paso N+3: Testing E2E con Playwright MCP (OBLIGATORIO si aplica)

**Responsabilidad del agente**: El agente de código DEBE ejecutar todos los tests E2E usando las herramientas de Playwright MCP. Esto NO es opcional y no puede delegarse al usuario.

**Cuándo Aplica**:
- Cambios de frontend que afecten flujos de usuario
- Integración entre endpoints de frontend y backend
- Features de cara al usuario que requieran interacción con el navegador

**Pasos de Implementación** (el agente debe realizarlos):
1. **Preparar el Entorno de Test**:
   - Asegurar que tanto el servidor de frontend como el de backend estén corriendo (iniciarlos si hace falta)
   - Verificar que la base de datos esté en un estado conocido
   - Chequear las herramientas de Playwright MCP disponibles usando el sistema de archivos de MCP

2. **Navegar a la Aplicación**:
   - Usar `browser_navigate` de Playwright MCP para abrir la URL de la aplicación
   - Esperar a que la página cargue completamente
   - Tomar un snapshot para verificar el estado inicial

3. **Ejecutar Flujos de Usuario**:
   - Usar las herramientas de Playwright MCP para interactuar con la UI:
     - `browser_click` para clics en botones y navegación
     - `browser_type` o `browser_fill` para inputs de formulario
     - `browser_snapshot` para verificar cambios de estado
     - `browser_wait` para operaciones asíncronas
   - Testear el flujo de usuario completo de principio a fin
   - Verificar los resultados esperados en cada paso

4. **Testear Escenarios de Error**:
   - Testear errores de validación de formularios
   - Testear que los mensajes de error se muestren correctamente
   - Testear los flujos de recuperación de error

5. **Verificar Persistencia de Datos**:
   - Después de crear/actualizar datos a través de la UI, verificar que persistan correctamente
   - Chequear que el estado de la base de datos coincida con el estado de la UI
   - Verificar que los datos aparezcan correctamente en las vistas de listas/detalles

6. **Restaurar el Entorno de Test**:
   - Limpiar cualquier dato de test creado durante los tests E2E
   - Restaurar la base de datos a su estado original
   - Cerrar las sesiones de navegador

7. **Marcar la Tarea como Completada**: Solo después de que todos los tests E2E pasen y el entorno esté restaurado, marcar la tarea como completada en `tasks.md`

**Dependencias**:
- Servidor de frontend corriendo (el agente debe iniciarlo si hace falta)
- Servidor de backend corriendo (el agente debe iniciarlo si hace falta)
- Herramientas de Playwright MCP disponibles
- Acceso a la base de datos para verificación y limpieza

**Notas**:
- **El agente DEBE ejecutar todos los tests E2E él mismo** — nunca pedirle al usuario que corra los tests
- Usar esperas incrementales (1-3 segundos) con chequeos de snapshot en vez de esperas largas
- Siempre restaurar el estado de la base de datos después de tests que modifiquen datos
- Documentar los escenarios y resultados de test en un reporte dentro de la carpeta de specs con el nombre apropiado
- **La tarea en tasks.md solo puede marcarse como completada después de la ejecución exitosa de todos los tests E2E**

## 4. Checklist de Verificación

Antes de finalizar cualquier archivo `tasks.md`, verificar:
- [ ] El Paso 0 (Crear Feature Branch) es el PRIMER paso
- [ ] Todos los pasos obligatorios de config.yaml están incluidos
- [ ] Los pasos están numerados secuencialmente
- [ ] Los pasos obligatorios están claramente marcados con la etiqueta "(OBLIGATORIO)"
- [ ] La nomenclatura de branch sigue la convención: `feature/[change-name]-backend` o `feature/[change-name]-<microfrontend>`
- [ ] El Paso N+1 incluye la ruta y el patrón de nombre del reporte en `specs/<change-name>/reports/`
- [ ] Los pasos de testing manual indican explícitamente "EL AGENTE DEBE EJECUTARLO"
- [ ] Las tareas incluyen pasos de restauración de estado de base de datos
- [ ] El paso de testing E2E está incluido si hay cambios de frontend involucrados

## 5. Cuándo Aplica Esta Regla

Esta regla aplica cuando:
- Se crea `tasks.md` vía `/opsx:ff` (fast-forward) o el skill `openspec-ff-change`
- Se crea `tasks.md` vía `/opsx:continue` o el skill `openspec-continue-change`
- Se actualizan archivos `tasks.md` existentes
- Cualquier creación de tareas que involucre cambios de backend
- Se implementan tareas de `tasks.md` vía `/opsx:apply` o el skill `openspec-apply-change` — el agente debe ejecutar los tests manuales

## 6. Estructura de Ejemplo

```markdown
## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [ ] 0.1 Crear el feature branch `feature/update-position-backend` desde main/master
- [ ] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: Tests de Validador (TDD)
...

## 8. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)
...

## 9. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)
- [ ] 9.1 Capturar el baseline de base de datos pre-test para las entidades impactadas
- [ ] 9.2 Correr los unit tests focalizados para los módulos modificados
- [ ] 9.3 Correr la suite de unit tests más amplia requerida por config
- [ ] 9.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [ ] 9.5 Crear el reporte `specs/<change-name>/reports/YYYY-MM-DD-step-N+1-unit-test-and-db-verification.md`
- [ ] 9.6 Marcar el paso como completo solo después de que los tests pasen y el reporte exista

## 10. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)
- [ ] 10.1 Asegurar que el servidor backend esté corriendo
- [ ] 10.2 Testear endpoints GET con curl y verificar las respuestas
- [ ] 10.3 Testear endpoints POST con curl, verificar la creación, luego restaurar el estado de la base de datos
- [ ] 10.4 Testear endpoints PUT/PATCH con curl, verificar las actualizaciones, luego restaurar el estado de la base de datos
- [ ] 10.5 Testear endpoints DELETE con curl, verificar la eliminación, luego restaurar el estado de la base de datos
- [ ] 10.6 Testear casos de error (errores de validación, 404, etc.)
- [ ] 10.7 Documentar todos los comandos curl y respuestas
- [ ] 10.8 Verificar que el estado de la base de datos coincida con el estado pre-test

## 11. Frontend: Testing E2E con Playwright MCP (OBLIGATORIO si aplica - EL AGENTE DEBE EJECUTARLO)
- [ ] 11.1 Asegurar que los servidores de frontend y backend estén corriendo
- [ ] 11.2 Navegar a la aplicación usando browser_navigate de Playwright MCP
- [ ] 11.3 Ejecutar el flujo de usuario completo usando las herramientas de Playwright MCP
- [ ] 11.4 Testear escenarios de error y validación
- [ ] 11.5 Verificar la persistencia de datos y el estado de la UI
- [ ] 11.6 Restaurar el entorno de test y el estado de la base de datos
- [ ] 11.7 Documentar los escenarios y resultados de test

## 16. Actualizar Documentación Técnica (OBLIGATORIO)
...
```

## 7. Requisitos de Ejecución del Agente

**CRÍTICO**: Al implementar tareas de `tasks.md` (vía el skill `openspec-apply-change` o el comando `/opsx:apply`), el agente de código DEBE:

1. **Ejecutar Todos los Tests Manuales**: Nunca pedirle al usuario que corra comandos curl o tests E2E. El agente debe:
   - Iniciar los servidores si hace falta (backend, frontend)
   - Ejecutar todos los comandos curl para el testing de endpoints
   - Ejecutar todos los tests E2E usando las herramientas de Playwright MCP
   - Verificar todas las respuestas y resultados
   - Restaurar el estado de la base de datos después de los tests

2. **Marcar Tareas como Completadas**: Las tareas SOLO pueden marcarse como completadas (`[x]`) en `tasks.md` DESPUÉS de que:
   - El agente haya ejecutado exitosamente todos los tests requeridos
   - Todos los resultados de test hayan sido verificados
   - El estado de la base de datos haya sido restaurado (para operaciones CREATE/UPDATE/DELETE)
   - Todos los resultados de test hayan sido documentados

3. **Nunca Delegar el Testing**: El agente nunca debe:
   - Pedirle al usuario que corra comandos curl
   - Pedirle al usuario que testee endpoints manualmente
   - Pedirle al usuario que corra tests E2E
   - Marcar tareas como completadas sin ejecutar los tests
   - Saltarse los pasos de testing manual

4. **Documentar la Ejecución de Tests**: El agente debe documentar:
   - Todos los comandos curl ejecutados
   - Todas las respuestas recibidas
   - Todos los escenarios de test E2E ejecutados
   - Las acciones de restauración de estado de la base de datos
   - Cualquier issue encontrado y su resolución

## Incumplimiento

Si creás tareas sin seguir estos pasos obligatorios, el usuario va a tener que corregir manualmente el archivo `tasks.md`. Siempre leé `openspec/config.yaml` primero y asegurate de que todos los pasos obligatorios estén incluidos.

**Si implementás tareas sin ejecutar los tests manuales vos mismo, estás violando esta regla. El agente debe ejecutar todos los tests para poder marcar las tareas como completadas.**