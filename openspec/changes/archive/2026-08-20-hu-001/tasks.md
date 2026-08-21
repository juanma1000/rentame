## 0. Setup: Crear Feature Branch — Backend (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear el feature branch `feature/hu-001-backend` desde main
- [x] 0.2 Verificar la creación del branch y el estado del branch actual
- [x] 0.3 Bootstrap del proyecto backend (no existe todavía en el repo): `pyproject.toml`, dependencias (FastAPI, SQLAlchemy async, Alembic, pytest, pytest-asyncio, httpx, boto3, python-jose), estructura hexagonal base de `docs/architecture/architecture.md` (`shared/`, `main.py`), `docker-compose.yml` con PostgreSQL y MinIO para desarrollo local, `alembic init`
- [x] 0.4 Verificar que el backend arranca (`uvicorn main:app`) y que `docker-compose up -d` deja Postgres y MinIO accesibles
- [x] 0.5 Stub mínimo de `usuarios` (no cubierto por ninguna HU todavía — registro/login quedan fuera de alcance): tabla `usuario` (id, email, rol) vía migración Alembic, `shared/infrastructure/auth/jwt_handler.py` (emitir/validar JWT con `sub`=usuario_id y claim `rol`) y `dependencies.py` (`get_current_propietario`). Incluir un helper de test para emitir JWT válidos dado un `usuario_id`/rol, y un seed mínimo de un usuario propietario de prueba

## 1. Backend: Dominio `inmuebles` — Tests (TDD - Red)

- [x] 1.1 Test: `Inmueble` se crea válido con estado `disponible` cuando todos los campos requeridos son válidos
- [x] 1.2 Test: `Inmueble` rechaza valor mensual <= 0
- [x] 1.3 Test: `Inmueble` rechaza habitaciones o baños negativos
- [x] 1.4 Test: `Inmueble` rechaza menos de 1 foto o más de 10 fotos (`MAX_FOTOS_INMUEBLE`)
- [x] 1.5 Test: transición de estado `disponible` → `oculto` (despublicar) es válida
- [x] 1.6 Test: transición de estado `oculto` → `disponible` (republicar) es válida
- [x] 1.7 Test: transición de estado a `no_disponible` es válida desde `disponible`

## 2. Backend: Dominio `inmuebles` — Implementación (TDD - Green/Refactor)

- [x] 2.1 Implementar entidad `Inmueble` y value object `FotoInmueble` (`backend/inmuebles/domain/`)
- [x] 2.2 Implementar `EstadoInmueble` enum y reglas de transición de estado
- [x] 2.3 Implementar `ports.py` (`InmuebleRepositoryPort`, `StoragePort`) y `exceptions.py` (`InmuebleNoEncontrado`, `PropietarioInvalido`, `LimiteFotosExcedido`)
- [x] 2.4 Confirmar que todos los tests de la sección 1 pasan (Green) y refactorizar si hace falta

## 3. Backend: Casos de Uso — Tests (TDD - Red)

- [x] 3.1 Test `publicar_inmueble`: crea inmueble con estado `disponible` y sube fotos vía `StoragePort` fake
- [x] 3.2 Test `publicar_inmueble`: rechaza cuando faltan campos requeridos o hay 0 fotos
- [x] 3.3 Test `editar_inmueble`: actualiza datos cuando el `propietario_id` coincide con el dueño
- [x] 3.4 Test `editar_inmueble`: rechaza cuando el `propietario_id` no coincide con el dueño
- [x] 3.5 Test `cambiar_disponibilidad`: cambia a `oculto` y a `disponible` (despublicar/republicar) por el propietario dueño
- [x] 3.6 Test `cambiar_disponibilidad`: cambia a `no_disponible` cuando se invoca directamente con un `inmueble_id` válido (simula el futuro caller de `arrendamiento`)
- [x] 3.7 Test `cambiar_disponibilidad`: rechaza cuando el `inmueble_id` no existe
- [x] 3.8 Test `listar_mis_inmuebles`: devuelve solo los inmuebles del `propietario_id` dado, con su estado actual
- [x] 3.9 Test `listar_mis_inmuebles`: devuelve lista vacía si el propietario no tiene inmuebles

## 4. Backend: Casos de Uso — Implementación (TDD - Green/Refactor)

- [x] 4.1 Implementar `publicar_inmueble.py`
- [x] 4.2 Implementar `editar_inmueble.py`
- [x] 4.3 Implementar `cambiar_disponibilidad.py`
- [x] 4.4 Implementar `listar_mis_inmuebles.py`
- [x] 4.5 Confirmar que todos los tests de la sección 3 pasan (Green) y refactorizar si hace falta

## 5. Backend: Persistencia

- [x] 5.1 Crear migración Alembic: tablas `inmueble` y `foto_inmueble` (según `docs/architecture/architecture.md`)
- [x] 5.2 Implementar `InmuebleORM` y `FotoInmuebleORM` (`infrastructure/persistence/models.py`)
- [x] 5.3 Implementar `InmuebleRepositoryPostgres` (`infrastructure/persistence/repository.py`)
- [x] 5.4 Tests de integración del repositorio contra base de datos de prueba: guardar, actualizar estado, filtrar por `propietario_id`

## 6. Backend: Storage Adapter

- [x] 6.1 Implementar `s3_storage_adapter.py` (`StoragePort` → boto3, MinIO local en dev)
- [x] 6.2 Test de integración: subir foto a MinIO local y obtener `storage_key`

## 7. Backend: API Layer

- [x] 7.1 Definir schemas Pydantic: `InmuebleCreateRequest` (multipart), `InmuebleResponse`, `InmuebleEditRequest`, `CambiarDisponibilidadRequest`
- [x] 7.2 Implementar dependencia de autenticación/ownership (`get_current_propietario`, valida JWT y extrae `propietario_id`)
- [x] 7.3 Implementar `POST /inmuebles/` (multipart: datos + 1 a 10 fotos)
- [x] 7.4 Implementar `PUT /inmuebles/{id}` (edición, valida ownership)
- [x] 7.5 Implementar `PATCH /inmuebles/{id}/disponibilidad` (despublicar/republicar, valida ownership)
- [x] 7.6 Implementar `GET /inmuebles/mios` (listado propio con estado)
- [x] 7.7 Tests de integración de cada endpoint vía `TestClient`, cubriendo los escenarios de `specs/inmuebles/spec.md` (éxito, validación, ownership, 404)

## 8. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 8.1 Revisar que ningún test previo del proyecto se vea afectado por el nuevo dominio `inmuebles`
- [x] 8.2 Actualizar/ajustar tests existentes si el nuevo código introdujo dependencias compartidas (`shared/domain`, `shared/infrastructure/auth`)

## 9. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 9.1 Capturar el baseline de base de datos pre-test (conteo de filas en `inmueble` y `foto_inmueble`, vacías al ser dominio nuevo)
- [x] 9.2 Correr los unit tests focalizados de `backend/inmuebles/` (dominio + casos de uso)
- [x] 9.3 Correr la suite completa de unit tests del backend (`pytest`) requerida por `openspec/config.yaml`, confirmando cobertura mínima 80% en la lógica de negocio nueva
- [x] 9.4 Verificar el estado post-test de la base de datos y restaurar si quedó alguna mutación no intencionada
- [x] 9.5 Crear el reporte `openspec/changes/hu-001/specs/reports/YYYY-MM-DD-step-9-unit-test-and-db-verification.md`
- [x] 9.6 Marcar esta sección como completa solo después de que los tests pasen y el reporte exista

## 10. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO — EL AGENTE DEBE EJECUTARLO)

- [x] 10.1 Levantar el servidor backend (`uvicorn`) y confirmar conexión a la base de datos
- [x] 10.2 `curl POST /inmuebles/` con datos y 1 foto válidos → verificar 201 y estado `disponible`; luego eliminar el registro creado para restaurar la base de datos
- [x] 10.3 `curl POST /inmuebles/` sin fotos → verificar 422/400 de validación
- [x] 10.4 `curl POST /inmuebles/` con 11 fotos → verificar 422/400 de validación
- [x] 10.5 `curl PUT /inmuebles/{id}` con el propietario dueño → verificar 200 y datos actualizados; restaurar valores originales
- [x] 10.6 `curl PUT /inmuebles/{id}` con un propietario distinto al dueño → verificar 403/404
- [x] 10.7 `curl PATCH /inmuebles/{id}/disponibilidad` despublicar y republicar → verificar cambios de estado `oculto`/`disponible`; restaurar estado original
- [x] 10.8 `curl GET /inmuebles/mios` con JWT del propietario → verificar que devuelve solo sus inmuebles con estado
- [x] 10.9 Documentar todos los comandos y respuestas en `openspec/changes/hu-001/specs/reports/YYYY-MM-DD-step-10-curl-manual-testing.md`
- [x] 10.10 Verificar que el estado de la base de datos coincide con el estado pre-test tras la limpieza

## 11. Setup: Crear Feature Branch — Shell + `@rentame/auth` (OBLIGATORIO)

- [x] 11.1 Crear el feature branch `feature/hu-001-shell` desde main
- [x] 11.2 Verificar la creación del branch y el estado del branch actual
- [x] 11.3 Bootstrap del monorepo frontend (no existe todavía en el repo): carpeta `frontend/` con workspaces (npm/pnpm), `packages/auth/` y `shell/` con `package.json`, TypeScript, Jest + React Testing Library, ESLint, y Rspack + `@module-federation/enhanced` como dependencias base
- [x] 11.4 Login mínimo de prueba: como `usuarios` no tiene UI/endpoint de login todavía (fuera de alcance de este change), `@rentame/auth` debe poder inicializar sesión a partir de un JWT provisto manualmente (ej. pantalla simple "pegar token" o variable de entorno de desarrollo) — documentar esta limitación en el README del frontend

## 12. Frontend: `@rentame/auth` — Tests (TDD - Red)

- [x] 12.1 Test: `AuthProvider` expone `null`/no-sesión cuando no hay JWT almacenado
- [x] 12.2 Test: `useAuth` expone el JWT y el rol del usuario cuando la sesión es válida
- [x] 12.3 Test: `AuthGuard` redirige a login cuando no hay sesión activa

## 13. Frontend: `@rentame/auth` — Implementación (TDD - Green/Refactor)

- [x] 13.1 Implementar `AuthProvider`, `useAuth`, `AuthGuard` en `packages/auth/`
- [x] 13.2 Configurar el paquete como `shared`/`singleton` en Module Federation (host y remotes)
- [x] 13.3 Confirmar que todos los tests de la sección 12 pasan (Green)

## 14. Frontend: `shell` (host) — Implementación mínima

- [x] 14.1 Configurar `rspack.config.ts` del host con Module Federation 2.0 y el remote `inmuebles-app` registrado
- [x] 14.2 Implementar router global y layout privado que exige sesión (usa `AuthGuard`)
- [x] 14.3 Test: navegación al layout privado sin sesión redirige a login
- [x] 14.4 Test: navegación al layout privado con sesión válida monta el remote correspondiente

## 15. Setup: Crear Feature Branch — `inmuebles-app` (OBLIGATORIO)

- [x] 15.1 Crear el feature branch `feature/hu-001-inmuebles-app` desde main
- [x] 15.2 Verificar la creación del branch y el estado del branch actual
- [x] 15.3 Bootstrap de `frontend/inmuebles-app/` (`package.json`, Rspack + Module Federation 2.0 como remote, dependencia de `@rentame/auth`, Jest + RTL)

## 16. Frontend: `inmuebles-app` — Formulario de Publicación (TDD)

- [x] 16.1 Test: el formulario deshabilita "Publicar" mientras falten campos requeridos
- [x] 16.2 Test: el formulario rechaza el envío con 0 fotos adjuntas
- [x] 16.3 Test: el formulario rechaza adjuntar más de 10 fotos
- [x] 16.4 Test: envío exitoso llama al servicio `inmuebles.api.ts` con multipart y muestra confirmación
- [x] 16.5 Implementar `PublicarInmueblePage.tsx`, `FileUpload` de fotos y `inmuebles.api.ts` (`publicar()`)
- [x] 16.6 Confirmar que todos los tests de la sección pasan (Green)

## 17. Frontend: `inmuebles-app` — Edición

- [x] 17.1 Test: formulario de edición precarga los datos actuales del inmueble
- [x] 17.2 Test: envío exitoso de edición llama a `inmuebles.api.ts` (`editar()`) y muestra confirmación
- [x] 17.3 Implementar página/formulario de edición reutilizando componentes del formulario de publicación

## 18. Frontend: `inmuebles-app` — Despublicar / Republicar

- [x] 18.1 Test: acción "despublicar" desde el panel llama a `cambiarDisponibilidad()` y refleja el nuevo estado en UI
- [x] 18.2 Test: acción "republicar" desde el panel llama a `cambiarDisponibilidad()` y refleja el nuevo estado en UI
- [x] 18.3 Implementar los controles de despublicar/republicar en `MisInmueblesPage.tsx`

## 19. Frontend: `inmuebles-app` — Panel "Mis Inmuebles"

- [x] 19.1 Test: renderiza la lista de inmuebles propios con badge de estado (`Disponible`/`No disponible`/`Despublicado`)
- [x] 19.2 Test: muestra estado vacío cuando el propietario no tiene inmuebles publicados
- [x] 19.3 Implementar `MisInmueblesPage.tsx` consumiendo `GET /inmuebles/mios`

## 20. Frontend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 20.1 Correr la suite completa de tests de Jest/RTL de `inmuebles-app`, `shell` y `packages/auth`
- [x] 20.2 Confirmar que no hay regresiones ni tests rotos por la integración entre remotes

## 21. Frontend + Integración: Testing E2E con Playwright MCP (OBLIGATORIO — EL AGENTE DEBE EJECUTARLO)

- [x] 21.1 Levantar backend, `shell`, `inmuebles-app` (y `packages/auth` compilado) en local
- [x] 21.2 Navegar a la app con `browser_navigate`, hacer login como propietario y verificar sesión activa
- [x] 21.3 Ejecutar flujo completo: publicar inmueble con 2 fotos → verificar que aparece en "Mis inmuebles" como `Disponible`
- [x] 21.4 Ejecutar flujo: editar el inmueble publicado → verificar los cambios reflejados
- [x] 21.5 Ejecutar flujo: despublicar el inmueble → verificar estado `Despublicado` → republicar → verificar estado `Disponible`
- [x] 21.6 Testear escenario de error: intentar publicar sin fotos y verificar mensaje de error en UI
- [x] 21.7 Verificar persistencia de datos comparando el estado de la base de datos con lo mostrado en la UI
- [x] 21.8 Restaurar el entorno de test (eliminar datos creados, restaurar base de datos) y documentar resultados en `openspec/changes/hu-001/specs/reports/YYYY-MM-DD-step-21-e2e-playwright.md`

## 22. Documentación (OBLIGATORIO)

- [x] 22.1 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-001-publicacion-inmueble-propietario.md`
- [x] 22.2 Actualizar la tabla de decisiones de `docs/architecture/architecture.md` para reflejar la resolución del mecanismo de subida de fotos (proxy por backend, no presigned URLs — ver `design.md` de este change)
- [x] 22.3 Documentar en el README del monorepo frontend (o crearlo si no existe) cómo levantar `shell` + `inmuebles-app` en local
