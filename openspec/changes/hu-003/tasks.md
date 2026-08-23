## 0. Setup: Crear Feature Branch Backend (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/hu-003-backend` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: Casos de uso públicos

- [x] 1.1 qa-expert (Red): tests unitarios de `listar_inmuebles_publicos` (fake repository) — solo devuelve `disponible`
- [x] 1.2 backend-expert (Green): `backend/inmuebles/application/listar_inmuebles_publicos.py`
- [x] 1.3 qa-expert (Red): tests unitarios de `obtener_inmueble_publico` (fake repository) — devuelve `None` si no existe o no está `disponible`
- [x] 1.4 backend-expert (Green): `backend/inmuebles/application/obtener_inmueble_publico.py`

## 2. Backend: Repositorio

- [x] 2.1 qa-expert (Red): test de integración de `InmuebleRepositoryPostgres.listar_disponibles()` contra Postgres real — mezcla de estados, solo devuelve `disponible`
- [x] 2.2 backend-expert (Green): método `listar_disponibles()` en `InmuebleRepositoryPort`/`InmuebleRepositoryPostgres`

## 3. Backend: Endpoints públicos

- [x] 3.1 qa-expert (Red): tests de integración `GET /inmuebles/publicos` — sin `Authorization`, solo disponibles, forma de la respuesta
- [x] 3.2 backend-expert (Green): endpoint `GET /inmuebles/publicos` + `InmueblePublicoListItemResponse` en `schemas.py`
- [x] 3.3 qa-expert (Red): tests de integración `GET /inmuebles/publicos/{id}` — éxito con todas las fotos, 404 si oculto/no_disponible/inexistente
- [x] 3.4 backend-expert (Green): endpoint `GET /inmuebles/publicos/{id}` + `InmueblePublicoResponse`

## 4. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 4.1 Revisar suite completa de `backend/tests/` en busca de fixtures/tests afectados por los cambios en `InmuebleRepositoryPort`/router — sin impacto, cambios puramente aditivos (nuevo método de repositorio, nuevas rutas, ningún schema/columna tocado)
- [x] 4.2 Actualizar fixtures si corresponde — no se requirió ningún cambio

## 5. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 5.1 Capturar el baseline de base de datos pre-test (conteo de filas en `inmueble`)
- [x] 5.2 Correr los unit tests focalizados de `inmuebles` vía `docker compose exec backend pytest backend/tests/inmuebles`
- [x] 5.3 Correr la suite completa vía `docker compose exec backend pytest`
- [x] 5.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [x] 5.5 Crear el reporte `openspec/changes/hu-003/specs/reports/YYYY-MM-DD-step-5-unit-test-and-db-verification.md`
- [x] 5.6 Marcar este paso como completo solo después de que los tests pasen y el reporte exista

## 6. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 6.1 Asegurar que `docker compose up` esté corriendo (backend + postgres)
- [x] 6.2 Testear `GET /inmuebles/publicos` con curl sin header de `Authorization`, verificar que solo aparecen los `disponible` (usar los inmuebles sembrados por `backend/scripts/seed_data.py`)
- [x] 6.3 Testear `GET /inmuebles/publicos/{id}` con curl para un inmueble `disponible` — verificar todas las fotos en la respuesta
- [x] 6.4 Testear `GET /inmuebles/publicos/{id}` para un inmueble `oculto` (usar el sembrado por el seed) — verificar 404
- [x] 6.5 Testear `GET /inmuebles/publicos/{id}` con un id inexistente — verificar 404
- [x] 6.6 Documentar todos los comandos curl y respuestas en `openspec/changes/hu-003/specs/reports/YYYY-MM-DD-step-6-curl-manual-testing.md`

## 7. Setup: Crear Feature Branch Frontend

- [x] 7.1 Crear y cambiar al branch `feature/hu-003-shell` desde `feature/hu-003-backend` (o desde `main` si ya se mergeó)
- [x] 7.2 Verificar la creación del branch y el estado del branch actual

## 8. Frontend (inmuebles-app): Cliente público y componente `BusquedaPublica`

- [x] 8.1 qa-expert (Red): tests de `inmuebles.api.ts` — `listarPublicos()`/`obtenerPublico(id)` (nuevas funciones, sin token)
- [x] 8.2 frontend-expert (Green): agregar `listarPublicos`/`obtenerPublico` a `frontend/inmuebles-app/src/services/inmuebles.api.ts`
- [x] 8.3 qa-expert (Red): tests RTL de `BusquedaPublica` — grid de tarjetas, clic navega al detalle, detalle muestra todas las fotos, inmueble sin coincidencias no crashea
- [x] 8.4 frontend-expert (Green): `frontend/inmuebles-app/src/pages/BusquedaPublicaPage.tsx` + componente de detalle, expuestos como `BusquedaPublica` en `rspack.config.ts` (`exposes`)

## 9. Frontend (shell): Nueva landing y reubicación de `EntradaPage`

- [x] 9.1 qa-expert (Red): tests RTL de la nueva página de landing del shell — monta el header (Publicar mi inmueble / Iniciar sesión) + lazy-carga `BusquedaPublica`
- [x] 9.2 frontend-expert (Green): `frontend/shell/src/pages/BusquedaPublicaShellPage.tsx` (o nombre equivalente) con el header, lazy-cargando `inmueblesApp/BusquedaPublica`
- [x] 9.3 frontend-expert: actualizar `frontend/shell/src/App.tsx` — `/` monta la nueva página de landing, `/publicar` monta `EntradaPage` (reubicada), resto de rutas sin cambios
- [x] 9.4 frontend-expert: actualizar `frontend/shell/rspack.config.ts` si se necesita declarar el nuevo remote expuesto por `inmuebles-app` (revisar `remotes`)

## 10. Frontend: Testing E2E con Playwright MCP (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 10.1 Asegurar que `docker compose up` esté corriendo (shell, inmuebles-app, backend, postgres) con rebuild de las imágenes tras los cambios
- [x] 10.2 E2E: visitante sin sesión navega a "/" y ve el listado de inmuebles sembrados en estado disponible
- [x] 10.3 E2E: clic en una tarjeta abre el detalle público con todas sus fotos
- [x] 10.4 E2E: un inmueble sembrado en estado `oculto` no aparece en el listado público
- [x] 10.5 E2E: clic en "Publicar mi inmueble" navega a `/publicar` y muestra `EntradaPage` (las 3 opciones de rol)
- [x] 10.6 E2E: clic en "Iniciar sesión" navega a `/login` y el flujo de login sigue funcionando sin cambios
- [x] 10.7 Restaurar el entorno (sin datos de prueba nuevos si el E2E solo lee el seed existente; limpiar cualquier dato creado)
- [x] 10.8 Documentar los escenarios y resultados en `openspec/changes/hu-003/specs/reports/YYYY-MM-DD-step-10-e2e-playwright.md`

## 11. Documentación (OBLIGATORIO)

- [x] 11.1 Actualizar `docs/architecture/architecture.md` con los 2 endpoints públicos nuevos, el componente `BusquedaPublica` en `inmuebles-app`, y la nueva estructura de rutas del `shell`
- [x] 11.2 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-003-busqueda-inmuebles-disponibles.md`
