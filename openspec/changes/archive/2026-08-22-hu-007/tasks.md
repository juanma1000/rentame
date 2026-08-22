## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear el feature branch `feature/hu-007-backend` desde main
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Dominio `agencias` — Tests (TDD - Red)

- [x] 1.1 Test: `Agencia` se crea válida con razón social y NIT
- [x] 1.2 Test: `RelacionAgenciaPropietario` se crea en estado `pendiente`
- [x] 1.3 Test: `RelacionAgenciaPropietario.activar()` transiciona de `pendiente` a `activa`
- [x] 1.4 Test: `RelacionAgenciaPropietario.activar()` rechaza si el estado no es `pendiente`
- [x] 1.5 Test: `RelacionAgenciaPropietario.revocar()` transiciona de `activa` a `revocada`
- [x] 1.6 Test: `RelacionAgenciaPropietario.revocar()` rechaza si el estado no es `activa`
- [x] 1.7 Test: `RelacionAgenciaPropietario.reasignar_responsable(nuevo_agente_id)` cambia el puntero sin cambiar el estado
- [x] 1.8 Test: `SolicitudIngreso` se crea en estado `pendiente`
- [x] 1.9 Test: `SolicitudIngreso.aprobar()` transiciona a `aprobada`

## 2. Dominio `agencias` — Implementación (TDD - Green/Refactor)

- [x] 2.1 Implementar `Agencia` (`backend/agencias/domain/agencia.py`)
- [x] 2.2 Implementar `RelacionAgenciaPropietario` con enum de estados y transiciones (`backend/agencias/domain/relacion_agencia_propietario.py`)
- [x] 2.3 Implementar `SolicitudIngreso` (`backend/agencias/domain/solicitud_ingreso.py`)
- [x] 2.4 Implementar `ports.py` (`AgenciaRepositoryPort`, `RelacionRepositoryPort`, `SolicitudIngresoRepositoryPort`) y `exceptions.py` (`AgenteYaTieneAgencia`, `AgenciaNoEncontrada`, `UltimoAgenteConRelacionesActivas`, `SolicitudNoEncontrada`, `RelacionYaActiva`, `RelacionNoEncontrada`)
- [x] 2.5 Confirmar que todos los tests de la sección 1 pasan (Green) y refactorizar si hace falta

## 3. Casos de Uso — Tests (TDD - Red)

- [x] 3.1 Test `crear_agencia`: crea agencia y asigna al agente creador como primer miembro (`usuario.agencia_id`)
- [x] 3.2 Test `crear_agencia`: rechaza (`AgenteYaTieneAgencia`) si el agente ya pertenece a una agencia
- [x] 3.3 Test `solicitar_ingreso`: crea solicitud pendiente si el agente no tiene agencia
- [x] 3.4 Test `solicitar_ingreso`: rechaza si el agente ya pertenece a una agencia
- [x] 3.5 Test `aprobar_ingreso`: un miembro de la agencia aprueba y el solicitante queda vinculado (`usuario.agencia_id` actualizado)
- [x] 3.6 Test `aprobar_ingreso`: rechaza si quien aprueba no es miembro de esa agencia
- [x] 3.7 Test `salir_de_agencia`: agente sale sin aprobación cuando hay más de un miembro
- [x] 3.8 Test `salir_de_agencia`: rechaza (`UltimoAgenteConRelacionesActivas`) si es el último miembro y la agencia tiene relaciones activas
- [x] 3.9 Test `salir_de_agencia`: permite la salida del último miembro si no hay relaciones activas
- [x] 3.10 Test `iniciar_relacion`: propietario inicia relación con agencia en estado `pendiente`
- [x] 3.11 Test `confirmar_relacion`: agente miembro confirma y la relación pasa a `activa`
- [x] 3.12 Test `confirmar_relacion`: si el propietario tenía otra relación `activa` previa, la revoca automáticamente (usando fakes de `inmuebles.listar_mis_inmuebles`/`cambiar_disponibilidad` para verificar que se invocan)
- [x] 3.13 Test `confirmar_relacion`: rechaza si quien confirma no es miembro de esa agencia
- [x] 3.14 Test `revocar_relacion`: propietario revoca su relación activa sin aprobación de la agencia
- [x] 3.15 Test `revocar_relacion`: dispara la cascada de despublicación llamando a `inmuebles.cambiar_disponibilidad(inmueble_id, OCULTO, propietario_id=None)` solo para los inmuebles gestionados por agentes de esa agencia (fake de `inmuebles`, verificar argumentos exactos)
- [x] 3.16 Test `revocar_relacion`: NO llama a `cambiar_disponibilidad` para inmuebles del propietario publicados sin agente (agente_id nulo)
- [x] 3.17 Test `reasignar_responsable`: cualquier miembro de la agencia reasigna a otro miembro
- [x] 3.18 Test `reasignar_responsable`: rechaza si el nuevo responsable no es miembro de la misma agencia

## 4. Casos de Uso — Implementación (TDD - Green/Refactor)

- [x] 4.1 Implementar `crear_agencia.py`
- [x] 4.2 Implementar `solicitar_ingreso.py` y `aprobar_ingreso.py`
- [x] 4.3 Implementar `salir_de_agencia.py`
- [x] 4.4 Implementar `iniciar_relacion.py`
- [x] 4.5 Implementar `confirmar_relacion.py` (incluye auto-revocación de relación activa previa + disparo de cascada)
- [x] 4.6 Implementar `revocar_relacion.py` (incluye disparo de cascada)
- [x] 4.7 Implementar `reasignar_responsable.py`
- [x] 4.8 Implementar el helper compartido de cascada de despublicación (usado por 4.5 y 4.6) que llama a `inmuebles.application.listar_mis_inmuebles` y `inmuebles.application.cambiar_disponibilidad`
- [x] 4.9 Confirmar que todos los tests de la sección 3 pasan (Green) y refactorizar si hace falta

## 5. Persistencia

- [x] 5.1 Crear migración Alembic: tablas `agencia`, `solicitud_ingreso_agencia`, `relacion_agencia_propietario`, y columna `usuario.agencia_id` (FK nullable a `usuario`, solo aplica a `rol=agente`)
- [x] 5.2 Implementar `AgenciaORM`, `SolicitudIngresoAgenciaORM`, `RelacionAgenciaPropietarioORM` (`agencias/infrastructure/persistence/models.py`); actualizar `UsuarioORM` con `agencia_id`
- [x] 5.3 Implementar `AgenciaRepositoryPostgres`, `RelacionRepositoryPostgres`, `SolicitudIngresoRepositoryPostgres`
- [x] 5.4 Tests de integración de los repositorios contra base de datos de prueba real: guardar/consultar agencia, transiciones de relación, listar agentes por `agencia_id`

## 6. Autenticación: `get_current_agente`

- [x] 6.1 Test: `get_current_agente` acepta JWT válido con rol `agente`
- [x] 6.2 Test: `get_current_agente` rechaza (401/403) JWT sin rol `agente`, ausente o inválido
- [x] 6.3 Implementar `get_current_agente` en `shared/infrastructure/auth/dependencies.py`, sin modificar `get_current_propietario`
- [x] 6.4 Correr la suite completa de `shared/infrastructure/auth` (incluye los tests ya existentes de HU-001) y confirmar cero regresiones

## 7. API Layer

- [x] 7.1 Definir schemas Pydantic: `AgenciaCreateRequest`, `AgenciaResponse`, `SolicitudIngresoRequest`, `SolicitudIngresoResponse`, `RelacionResponse`, `ReasignarResponsableRequest`
- [x] 7.2 Implementar `POST /agencias/` (crear agencia, requiere `get_current_agente`)
- [x] 7.3 Implementar `POST /agencias/{id}/solicitudes` (solicitar ingreso) y `POST /agencias/solicitudes/{id}/aprobar` (aprobar ingreso)
- [x] 7.4 Implementar `POST /agencias/salir` (salida voluntaria del agente autenticado)
- [x] 7.5 Implementar `POST /agencias/{id}/relaciones` (propietario inicia relación, requiere `get_current_propietario`)
- [x] 7.6 Implementar `POST /agencias/relaciones/{id}/confirmar` (agente confirma) y `POST /agencias/relaciones/{id}/revocar` (propietario revoca)
- [x] 7.7 Implementar `PATCH /agencias/relaciones/{id}/responsable` (reasignar agente responsable)
- [x] 7.8 Implementar `GET /agencias/mia/propietarios` (listado de propietarios vinculados a la agencia del agente autenticado)
- [x] 7.9 Tests de integración de cada endpoint vía `TestClient`, cubriendo los escenarios de `specs/agencias/spec.md` y el escenario de cascada de `specs/inmuebles/spec.md` (verificando el estado real del inmueble en la base de datos tras revocar)

## 8. Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 8.1 Revisar que ningún test previo del proyecto (55 de `inmuebles`/`shared`/`usuarios` de HU-001) se vea afectado por el nuevo dominio `agencias`
- [x] 8.2 Confirmar que `inmuebles.application.cambiar_disponibilidad` y `listar_mis_inmuebles` no fueron modificados, solo consumidos por `agencias`

## 9. Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 9.1 Capturar el baseline de base de datos pre-test (conteo de filas en `agencia`, `solicitud_ingreso_agencia`, `relacion_agencia_propietario`, y en `usuario`/`inmueble` para confirmar que no cambian por accidente)
- [x] 9.2 Correr los unit tests focalizados de `backend/agencias/` (dominio + casos de uso)
- [x] 9.3 Correr la suite completa de unit tests del backend (`pytest`), confirmando cobertura mínima 80% en la lógica de negocio nueva y cero regresiones sobre los 55 tests previos
- [x] 9.4 Verificar el estado post-test de la base de datos y restaurar si quedó alguna mutación no intencionada
- [x] 9.5 Crear el reporte `openspec/changes/hu-007/specs/reports/YYYY-MM-DD-step-9-unit-test-and-db-verification.md`
- [x] 9.6 Marcar esta sección como completa solo después de que los tests pasen y el reporte exista

## 10. Testing Manual de Endpoints con curl (OBLIGATORIO — EL AGENTE DEBE EJECUTARLO)

- [x] 10.1 Levantar el backend (vía Docker, ya dockerizado desde el change de HU-001 — NO usar venv local) y confirmar conexión a la base de datos
- [x] 10.2 `curl POST /agencias/` con un agente sin agencia → verificar 201 y que el agente queda vinculado; `curl POST /agencias/` con el mismo agente de nuevo → verificar rechazo
- [x] 10.3 `curl POST /agencias/{id}/solicitudes` con un segundo agente → verificar pendiente; `curl POST /agencias/solicitudes/{id}/aprobar` con el primer agente → verificar que el segundo queda vinculado
- [x] 10.4 `curl POST /agencias/{id}/relaciones` (propietario) → `curl POST /agencias/relaciones/{id}/confirmar` (agente) → verificar estado `activa`
- [x] 10.5 Publicar (directo en DB de test, ya que HU-002 no existe todavía) un inmueble con `agente_id` de ese agente → `curl POST /agencias/relaciones/{id}/revocar` (propietario) → verificar con `curl GET` sobre el inmueble que quedó en estado `oculto`
- [x] 10.6 `curl POST /agencias/{id}/relaciones` con una segunda agencia y confirmarla → verificar que la primera relación pasa a `revocada` automáticamente y que se repite la despublicación en cascada
- [x] 10.7 `curl POST /agencias/salir` con el único agente restante de una agencia con relación activa → verificar rechazo; revocar la relación y reintentar → verificar que sí puede salir
- [x] 10.8 Restaurar la base de datos al estado pre-test (eliminar agencias/relaciones/solicitudes/usuarios de prueba creados)
- [x] 10.9 Documentar todos los comandos y respuestas en `openspec/changes/hu-007/specs/reports/YYYY-MM-DD-step-10-curl-manual-testing.md`
- [x] 10.10 Verificar que el estado de la base de datos coincide con el estado pre-test tras la limpieza

## 11. Documentación (OBLIGATORIO)

- [x] 11.1 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-007-gestion-de-agencias.md`
- [x] 11.2 Actualizar `docs/architecture/architecture.md`: agregar el dominio `agencias` a la estructura de carpetas backend y las tablas nuevas al diagrama ER
- [x] 11.3 Anotar en `docs/user-stories/HU-002-publicacion-inmueble-agente.md` que su bloqueo (dependencia de HU-007) quedó resuelto, sin cambiar su alcance
