# Reporte Paso 10 - Testing E2E con Playwright MCP

- Fecha: 2026-08-22
- Cambio: hu-003
- Agente: Claude Code (Playwright MCP real)

Entorno: `docker compose up` con `shell`, `inmuebles-app` y `backend` reconstruidos con el código de `hu-003`, `postgres`, `minio`.

## Bug real encontrado y corregido durante el E2E

Al cargar la landing pública, las 3 fotos fallaban con `ERR_NAME_NOT_RESOLVED` para URLs `http://minio:9000/...`. Causa: `S3StorageAdapter.construir_url()` y el script de seed usaban `settings.storage_endpoint_url` (el hostname interno de la red Docker, `http://minio:9000`, usado por el backend para hablar con MinIO) también para las URLs devueltas al cliente — un hostname que el navegador nunca puede resolver. Este problema ya existía desde HU-001 pero nunca era visible: ninguna página autenticada anterior renderizaba `<img>` con esas URLs de forma directamente comprobable en un flujo E2E hasta esta landing pública.

**Corregido**: nueva setting `storage_public_url` (`backend/shared/infrastructure/settings.py`), usada por `S3StorageAdapter.construir_url()` con fallback a `storage_endpoint_url` si no está configurada. `docker-compose.yml` ahora setea `STORAGE_PUBLIC_URL=http://localhost:9000` para el backend (browser-reachable), dejando `STORAGE_ENDPOINT_URL=http://minio:9000` sin cambios para las llamadas internas backend→MinIO. `backend/scripts/seed_data.py` actualizado para usar la misma prioridad. 2 tests de regresión agregados en `test_storage_adapter.py`. Re-verificado: 0 errores de consola tras el fix.

## Escenarios ejecutados

### 10.2 — Visitante sin sesión ve el listado
`http://localhost:3000/` muestra 3 tarjetas (las 3 con `estado=disponible` sembradas), cada una con foto, dirección/barrio, ciudad, precio, habitaciones, baños. Header con "Publicar mi inmueble" / "Iniciar sesión".

### 10.3 — Detalle público con todas las fotos
Clic en "Calle 10 # 5-30" → vista de detalle con las 2 fotos, descripción completa, área, habitaciones, baños, precio. Botón "Volver" regresa al listado.

### 10.4 — Un inmueble oculto no aparece
"Calle 33 # 70-15" (sembrado en estado `oculto`) no aparece en el listado de 3 tarjetas — confirmado también por curl en el reporte del paso 6.

### 10.5 — "Publicar mi inmueble" → `/publicar` → `EntradaPage`
Clic navega a `/publicar`, que muestra las 3 opciones de rol (propietario/agente/inquilino) — `EntradaPage` reubicada, sin cambios internos. Navegación directa (`browser_navigate` a `/publicar`, carga completa) también funciona sin errores de consola (confirma que el fix de `publicPath` de HU-008 sigue vigente para la ruta nueva).

### 10.6 — "Iniciar sesión" → `/login` sin cambios
Login con `ana.propietaria@seed.rentame.test` / `Seed1234!` redirige a `/mis-inmuebles` con sesión activa, comportamiento idéntico a antes de este change.

## Restauración del entorno
No se creó ningún dato de prueba durante el E2E (solo lecturas y un login, que no muta datos). Sin necesidad de limpieza.

## Resultado
- Estado del Paso 10: PASS
- Issue real encontrado y corregido: URLs de fotos usando el hostname interno de Docker en vez de uno accesible por el navegador (`storage_public_url` nuevo)
- Issues bloqueantes: ninguno
