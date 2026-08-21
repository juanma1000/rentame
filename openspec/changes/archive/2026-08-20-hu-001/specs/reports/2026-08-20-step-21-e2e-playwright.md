# Reporte Paso 21 - Testing E2E con Playwright MCP

- Fecha: 2026-08-20
- Cambio: hu-001
- Agente: Claude (sesión principal, herramientas Playwright MCP)

## Entorno

- Backend: `uvicorn main:app` en `http://localhost:8000`, Postgres + MinIO reales vía `docker compose`.
- Frontend: `shell` en `http://localhost:3000`, `inmuebles-app` en `http://localhost:3001` (remote Module Federation).
- Usuario de prueba: `usuario` propietario insertado directo en DB (`id=11111111-1111-1111-1111-111111111111`, rol `propietario`), JWT emitido con `backend/tests/utils/auth.py`.

## Bugs reales encontrados y corregidos durante esta fase

Ninguno de estos lo detectaron los 126 tests automatizados (55 backend + 71 frontend previos) porque todos corren contra mocks o fakes. Solo aparecieron al navegar con un browser real:

1. **`ReferenceError: process is not defined`** en el bundle de `inmuebles-app` — `process.env.INMUEBLES_API_URL` sin resolver en build de Rspack. Fix: `DefinePlugin` en `inmuebles-app/rspack.config.ts`.
2. **CORS bloqueado**: backend sin `CORSMiddleware`, todo fetch desde `localhost:3000` fallaba en preflight. Fix: `CORSMiddleware` agregado en `backend/main.py` + `cors_allowed_origins` en `settings.py`.
3. **Mapeo de respuesta roto**: las 4 funciones de `inmuebles.api.ts` devolvían `response.json()` sin convertir snake_case (real, del backend) a camelCase (`Inmueble`). Los mocks de test asumían camelCase, ocultando el bug. Síntoma visual: al editar, "Área en m²" y "Valor mensual" aparecían vacíos (los únicos campos cuyo nombre difiere entre convenciones). Fix: `mapInmuebleFromApi` + corrección de los fixtures de test (error genuino de test, confirmado con curl contra el backend real).
4. **Wiring faltante**: el shell nunca se conectó al remote real — mostraba un placeholder estático en `/mis-inmuebles`. Fix: `React.lazy` cargando `inmueblesApp/PropertyRoutes` real, con estado local de navegación (lista/publicar/editar) dentro del remote.

Los 3 primeros bugs habrían llegado a producción si el paso de testing manual (curl + E2E) se hubiera omitido — validación directa de por qué `openspec-tasks-mandatory-steps.md` los exige.

## Escenarios ejecutados

1. **Login por token** (`/`): pegar JWT válido → sesión inicializada, redirección exitosa a rutas protegidas.
2. **Navegación a `/mis-inmuebles` sin publicaciones**: lista vacía, mensaje "No tenés inmuebles publicados.", botón "Publicar nuevo inmueble" visible.
3. **Publicar inmueble** (flujo feliz): formulario completo (dirección, barrio, ciudad, tipo, área, habitaciones, baños, valor, descripción) + 1 foto real subida vía file chooser (desviación menor respecto al plan de 2 fotos — 1 foto ya ejercita el mínimo requerido; el máximo de 10 y el caso de 0 fotos están cubiertos por los tests unitarios de `PublicarInmueblePage` y por la verificación manual con curl del Paso 10) → botón "Publicar" se habilita → submit → vuelve a la lista → aparece la card con estado "Disponible".
4. **Despublicar**: click en "Despublicar" → estado cambia a "Despublicado" en la UI sin recarga completa, botón cambia a "Republicar".
5. **Republicar**: click en "Republicar" → estado vuelve a "Disponible", botón vuelve a "Despublicar".
6. **Editar**: click en "Editar" → formulario precargado con todos los campos (incluye la verificación explícita post-fix de "Área en m²" y "Valor mensual") → cambio de valor mensual (2.000.000 → 2.200.000) → "Guardar cambios" → vuelve a la lista.
7. **Verificación de persistencia real**: `curl GET /inmuebles/mios` confirma `valor_mensual: 2200000.0` en la base de datos, coincidiendo con lo mostrado en la UI.
8. **Escenario de error/validación**: formulario de publicación sin datos ni fotos → botón "Publicar" permanece deshabilitado (guardia de cliente ya cubierta por tests unitarios, reconfirmada en runtime real).

## Restauración de entorno

- `DELETE FROM foto_inmueble/inmueble WHERE ...` para el inmueble de prueba creado.
- `DELETE FROM usuario WHERE id='11111111-1111-1111-1111-111111111111'`.
- `mc rm --recursive` sobre el objeto subido a MinIO.
- Verificado post-limpieza: `inmueble`=0, `foto_inmueble`=0, `usuario`=0 — estado idéntico al baseline anterior a este paso.

## Resultado

- Estado del Paso 21: **PASS** (tras corregir los 4 bugs listados arriba, todos con fix aplicado y re-verificado en el mismo paso).
- Issues bloqueantes: ninguno pendiente.
- Regresión de tests automatizados tras los fixes: 55 backend + 82 frontend (tras el wiring) ajustado a 54 en `inmuebles-app` tras el fix de mapeo (los suites de páginas no cambiaron) — sin fallas.
