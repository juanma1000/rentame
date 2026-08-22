## 0. Setup: Crear Feature Branch — Backend (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear el feature branch `feature/hu-002-backend` desde main
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Dominio y Auth — Tests (TDD - Red)

- [x] 1.1 Test: `Inmueble.crear(..., agente_id=...)` acepta `agente_id` opcional, default `None`
- [x] 1.2 Test: `get_current_publicador` acepta JWT con rol `propietario`
- [x] 1.3 Test: `get_current_publicador` acepta JWT con rol `agente`
- [x] 1.4 Test: `get_current_publicador` rechaza JWT con cualquier otro rol, ausente o inválido

## 2. Dominio y Auth — Implementación (TDD - Green/Refactor)

- [x] 2.1 Agregar `agente_id` a `Inmueble.crear()` (`backend/inmuebles/domain/inmueble.py`), sin ninguna validación de negocio nueva
- [x] 2.2 Implementar `get_current_publicador` en `shared/infrastructure/auth/dependencies.py`, sin modificar `get_current_propietario` ni `get_current_agente`
- [x] 2.3 Confirmar que todos los tests de la sección 1 pasan (Green)

## 3. Casos de Uso — Tests (TDD - Red)

- [x] 3.1 Test `publicar_inmueble`: `PublicarInmuebleCommand` acepta `agente_id` opcional; al crearse, el `Inmueble` resultante tiene ese `agente_id`
- [x] 3.2 Test `editar_inmueble`: confirmar (test de regresión explícito) que `agente_id` del inmueble no cambia después de una edición, sin importar quién edite
- [x] 3.3 Test `listar_inmuebles_gestionados`: dado una lista de `propietario_id` ya resuelta, devuelve los inmuebles de esos propietarios con su estado
- [x] 3.4 Test `listar_inmuebles_gestionados`: devuelve lista vacía si la lista de propietarios está vacía
- [x] 3.5 Test de revisión de imports: `backend/inmuebles/application/*.py` no importa nada de `agencias` (test estático simple, ej. grep sobre el árbol de imports, o un test que falle si aparece `from agencias` en esos archivos)

## 4. Casos de Uso — Implementación (TDD - Green/Refactor)

- [x] 4.1 Actualizar `PublicarInmuebleCommand`/`publicar_inmueble.py` para aceptar y propagar `agente_id`
- [x] 4.2 Confirmar que `editar_inmueble.py`/`cambiar_disponibilidad.py` no requieren cambios de lógica (solo se les sigue pasando `propietario_id`, ahora resuelto por la API en vez de por el JWT directo — ver diseño)
- [x] 4.3 Implementar `listar_inmuebles_gestionados.py`
- [x] 4.4 Confirmar que todos los tests de la sección 3 pasan (Green)

## 5. Persistencia

- [x] 5.1 Implementar `InmuebleRepositoryPostgres.listar_por_propietarios(ids: list[UUID])` (nuevo método en `InmuebleRepositoryPort` y su implementación)
- [x] 5.2 Test de integración contra Postgres real: devuelve inmuebles de múltiples propietarios, excluye los de propietarios no listados, vacío si la lista está vacía

## 6. API Layer

- [x] 6.1 Ampliar `POST /inmuebles/`: usar `get_current_publicador`; si `rol=="agente"`, exigir `propietario_id` en el form y validar relación activa (consultando `agencias.RelacionRepository` + `UsuarioAgenciaRepository` inyectados); si `rol=="propietario"`, usar su propio id
- [x] 6.2 Ampliar `PUT /inmuebles/{id}`: resolver `propietario_id` real del inmueble primero; autorizar propietario dueño O agente con agencia activa; invocar el caso de uso con el `propietario_id` real
- [x] 6.3 Ampliar `PATCH /inmuebles/{id}/disponibilidad`: mismo patrón de autorización que 6.2
- [x] 6.4 Implementar `GET /inmuebles/gestionados`: resolver los `propietario_id` con relación activa con la agencia del agente (vía `agencias`), llamar a `listar_inmuebles_gestionados`
- [x] 6.5 Verificar si `RelacionResponse` (`agencias/infrastructure/api/schemas.py`) expone suficiente información del propietario (al menos `email`) para que el frontend pueda mostrar un selector legible; si no, ampliar ese schema de respuesta únicamente (sin tocar `agencias/application` ni `agencias/domain`)
- [x] 6.6 Tests de integración de cada endpoint ampliado/nuevo vía `TestClient` con Postgres real, cubriendo todos los escenarios de `specs/inmuebles/spec.md` de este change (agente con relación activa, agente sin relación activa, agente de otra agencia, propietario dueño sin cambios)

## 7. Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 7.1 Revisar que los 132 tests existentes (HU-001 + HU-007) sigan en verde sin verse afectados
- [x] 7.2 Confirmar que `agencias/application` y `agencias/domain` no fueron modificados por este change (solo se los consume desde `inmuebles/infrastructure/api`)

## 8. Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 8.1 Capturar baseline de base de datos pre-test en `inmueble` (conteo, ya que este change puede crear inmuebles con `agente_id` distinto de null por primera vez)
- [x] 8.2 Correr los tests focalizados de `inmuebles` y `shared/infrastructure/auth`
- [x] 8.3 Correr la suite completa (`pytest` con cobertura), confirmando mínimo 80% en la lógica nueva y cero regresiones sobre los 132 tests previos
- [x] 8.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [x] 8.5 Crear el reporte `openspec/changes/hu-002/specs/reports/2026-08-22-step-8-unit-test-and-db-verification.md`
- [x] 8.6 Marcar esta sección completa solo después de que los tests pasen y el reporte exista

## 9. Testing Manual de Endpoints con curl (OBLIGATORIO — EL AGENTE DEBE EJECUTARLO)

- [x] 9.1 Levantar el backend vía Docker (bind mount + `--reload`, NO venv local) y confirmar conexión a la base de datos
- [x] 9.2 Usando una agencia y relación activa creadas en el paso anterior (o nuevas de prueba): `curl POST /inmuebles/` como agente con `propietario_id` del propietario vinculado → 201, verificar `agente_id` en la respuesta
- [x] 9.3 `curl POST /inmuebles/` como agente con `propietario_id` de un propietario SIN relación activa → rechazo
- [x] 9.4 `curl PUT /inmuebles/{id}` como un segundo agente de la MISMA agencia (que no publicó el inmueble) → 200, verificar que `agente_id` en la respuesta sigue siendo el del agente original
- [x] 9.5 `curl PUT /inmuebles/{id}` como agente de OTRA agencia → rechazo
- [x] 9.6 `curl PATCH /inmuebles/{id}/disponibilidad` como agente con relación activa → verificar cambio de estado
- [x] 9.7 `curl GET /inmuebles/gestionados` como agente → verificar que devuelve solo los inmuebles de sus propietarios con relación activa
- [x] 9.8 Restaurar la base de datos al estado pre-test
- [x] 9.9 Documentar todos los comandos y respuestas en `openspec/changes/hu-002/specs/reports/YYYY-MM-DD-step-9-curl-manual-testing.md`
- [x] 9.10 Verificar que el estado de la base de datos coincide con el pre-test tras la limpieza

## 10. Setup: Crear Feature Branch — Frontend `inmuebles-app` (OBLIGATORIO)

- [x] 10.1 Crear el feature branch `feature/hu-002-inmuebles-app` desde main
- [x] 10.2 Verificar la creación del branch y el estado del branch actual

## 11. Frontend: Selector de Propietario (TDD)

- [x] 11.1 Test: `PublicarInmueblePage` muestra el selector de propietario solo cuando la sesión es de rol `agente` (usando `useAuth()`)
- [x] 11.2 Test: el selector se llena con los propietarios de `GET /agencias/mia/propietarios` con relación `activa`
- [x] 11.3 Test: el envío incluye el `propietario_id` seleccionado en el request a `publicarInmueble`
- [x] 11.4 Test: `EditarInmueblePage` no requiere selector (edita el inmueble existente, propietario ya fijo) pero sí debe permitir que un agente distinto al publicador la use
- [x] 11.5 Implementar el selector condicional por rol en `PublicarInmueblePage.tsx`, y el servicio `agencias.api.ts` (nuevo) o extensión de `inmuebles.api.ts` para consumir `GET /agencias/mia/propietarios`
- [x] 11.6 Confirmar que todos los tests de la sección pasan (Green)

## 12. Frontend: Panel "Inmuebles que gestiono" (TDD)

- [x] 12.1 Test: renderiza la lista de inmuebles gestionados con badge de estado, análogo a `MisInmueblesPage`
- [x] 12.2 Test: muestra estado vacío si el agente no gestiona ningún inmueble
- [x] 12.3 Implementar `InmueblesGestionadosPage.tsx` consumiendo `GET /inmuebles/gestionados`, reusando componentes de `MisInmueblesPage` donde tenga sentido sin sobre-abstraer
- [x] 12.4 Confirmar que todos los tests de la sección pasan (Green)

## 13. Revisar y Actualizar Unit Tests Existentes — Frontend (OBLIGATORIO)

- [x] 13.1 Correr la suite completa de Jest/RTL de `inmuebles-app`, `shell` y `@rentame/auth`
- [x] 13.2 Confirmar que no hay regresiones sobre los tests existentes de HU-001

## 14. Testing E2E con Playwright MCP (OBLIGATORIO — EL AGENTE DEBE EJECUTARLO)

- [ ] 14.1 Levantar backend, `shell`, `inmuebles-app` vía Docker
- [ ] 14.2 Flujo agente: login con JWT de agente → publicar inmueble seleccionando propietario → verificar que aparece en "Inmuebles que gestiono"
- [ ] 14.3 Flujo cruzado: un segundo agente de la misma agencia edita ese inmueble → verificar cambios reflejados
- [ ] 14.4 Verificar persistencia comparando el estado de la base de datos con lo mostrado en la UI
- [ ] 14.5 Restaurar el entorno de test y documentar en `openspec/changes/hu-002/specs/reports/YYYY-MM-DD-step-14-e2e-playwright.md`

## 15. Documentación (OBLIGATORIO)

- [ ] 15.1 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-002-publicacion-inmueble-agente.md`
- [ ] 15.2 Actualizar `docs/architecture/architecture.md` si la estructura de carpetas de `inmuebles`/`inmuebles-app` cambió de forma relevante (nuevo caso de uso, nuevo endpoint, nueva página)
