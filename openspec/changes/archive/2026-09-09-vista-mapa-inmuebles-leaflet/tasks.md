## 1. Dominio — `Inmueble` con coordenadas

- [x] 1.1 (Red) Test: `Inmueble.crear` acepta `latitud`/`longitud` opcionales (`None` por defecto).
- [x] 1.2 (Green) Agregar `latitud: Decimal | None` y `longitud: Decimal | None` al dataclass `Inmueble` (`domain/inmueble.py`), con default `None` en `crear`.
- [x] 1.3 (Red) Test: `Inmueble` expone un método para fijar/actualizar coordenadas (ej. `actualizar_coordenadas(latitud, longitud)`) sin pasar por `actualizar_datos`.
- [x] 1.4 (Green) Implementar `actualizar_coordenadas` en el agregado.
- [x] 1.5 (Refactor) Revisar que `_validar_datos` no necesite validar lat/lng (son opcionales y no tienen invariante de negocio propia en esta iteración).

## 2. Puerto de geocodificación

- [x] 2.1 Definir `Coordenadas` (dataclass simple: `latitud: Decimal`, `longitud: Decimal`) y `GeocodingPort` (Protocol con `async def geocodificar(self, *, direccion: str, barrio: str, ciudad: str) -> Coordenadas | None`) en `inmuebles/domain/ports.py`, documentando que nunca lanza (fallo = `None`).
- [x] 2.2 (Red) Test de contrato para `fake_adapter.py`: devuelve las coordenadas configuradas o `None` según se le indique, sin lanzar.
- [x] 2.3 (Green) Implementar `inmuebles/infrastructure/external/geocoding_fake_adapter.py` (mismo patrón que `identidad`/`pagos`/`seguro_arrendamiento`).
- [x] 2.4 (Red) Tests de `NominatimAdapter` contra un mock de `httpx.AsyncClient`: respuesta exitosa devuelve `Coordenadas`; timeout devuelve `None`; status >= 400 devuelve `None`; respuesta sin resultados (`[]`) devuelve `None`. Ninguno de los cuatro casos debe lanzar excepción.
- [x] 2.5 (Green) Implementar `inmuebles/infrastructure/external/nominatim_adapter.py`: `httpx.AsyncClient(timeout=10.0)`, GET a `https://nominatim.openstreetmap.org/search` con `q=` (dirección + barrio + ciudad concatenados) y `format=jsonv2`, header `User-Agent` identificando la app (requerido por la política de uso de Nominatim), parseo del primer resultado a `Coordenadas`.
- [x] 2.6 (Refactor) Confirmar que ningún camino de error del adaptador se escapa como excepción no capturada (revisar `httpx.HTTPError`, `KeyError`/`IndexError` al parsear un JSON vacío o inesperado).

## 3. Aplicación — publicar y editar con geocodificación

- [x] 3.1 (Red) Test: `publicar_inmueble` con `fake_adapter` configurado para devolver coordenadas → el `Inmueble` creado las tiene.
- [x] 3.2 (Red) Test: `publicar_inmueble` con `fake_adapter` configurado para devolver `None` → el `Inmueble` se crea igual, con `latitud`/`longitud` en `None`, sin lanzar ni propagar error.
- [x] 3.3 (Green) Inyectar `GeocodingPort` en `publicar_inmueble` (nuevo parámetro `geocoding: GeocodingPort`), invocarlo antes de `Inmueble.crear` y pasar el resultado (o `None`) al agregado.
- [x] 3.4 (Red) Test: `editar_inmueble` que cambia `direccion` invoca `GeocodingPort` y actualiza coordenadas.
- [x] 3.5 (Red) Test: `editar_inmueble` que NO cambia `direccion`/`barrio`/`ciudad` (mismos valores que ya tenía el inmueble) NO invoca `GeocodingPort` (verificar con spy/mock de llamadas) y conserva las coordenadas existentes.
- [x] 3.6 (Green) Inyectar `GeocodingPort` en `editar_inmueble`, comparar los tres campos de ubicación contra los valores actuales del inmueble antes de decidir si geocodifica.
- [x] 3.7 (Refactor) Extraer la lógica "¿cambió la ubicación?" a un helper reutilizado por ambos casos de uso si el duplicado lo justifica. — Sin duplicación real: `publicar_inmueble` siempre geocodifica (no hay condición que compartir) y la comparación en `editar_inmueble` se usa una sola vez; no se extrajo helper.

## 4. Infraestructura — persistencia y API

- [x] 4.1 Crear migración Alembic: agregar `latitud`, `longitud` (`Numeric`, nullable) a la tabla `inmueble`.
- [x] 4.2 (Red→verificación manual) La suite de tests de este proyecto usa `Base.metadata.create_all` contra la base de test (no Alembic) — no existe precedente de tests automatizados de migraciones. Se verificó manualmente contra la base de dev: `upgrade head` → `downgrade -1` → `upgrade head`, limpio.
- [x] 4.3 Actualizar `InmuebleORM` (`infrastructure/persistence/models.py`) y el mapeo en `repository.py` (`guardar`/`actualizar`/`obtener_por_id`/`listar_disponibles`, etc.) para incluir `latitud`/`longitud`.
- [x] 4.4 (Red) Test de `GET /inmuebles/publicos`: el DTO de respuesta incluye `latitud`/`longitud`, con caso `null`.
- [x] 4.5 (Green) Actualizar `infrastructure/api/schemas.py` (DTO de listado público) y `infrastructure/api/router.py` si hace falta mapeo explícito.
- [x] 4.6 Actualizar el punto de composición de dependencias (donde se instancian `publicar_inmueble`/`editar_inmueble` con sus puertos) para inyectar `NominatimAdapter` en runtime y `geocoding_fake_adapter` en tests — seguir el patrón ya usado para `identidad`/`pagos`/`seguro_arrendamiento` (selección por settings/env, ver cómo se resuelve `TruoraAdapter` vs. su fake hoy). Nuevo `inmuebles/infrastructure/proveedor.py` + `Settings.inmuebles_geocoding_proveedor` (default `"fake"`); `docker-compose.yml` lo fija en `"nominatim"` para dev, ya que a diferencia de Truora/Wompi/Sura no requiere API key.

## 5. Backfill de inmuebles existentes

- [x] 5.1 Escribir `backend/scripts/backfill_coordenadas_inmuebles.py` (estilo `scripts/seed_data.py`): recorre inmuebles con `latitud`/`longitud` en `null`, geocodifica cada uno con `NominatimAdapter` respetando el rate limit de 1 req/seg (esperar entre llamadas, a diferencia del flujo de publicación que no lo hace porque es un solo request), actualiza y hace commit.
- [x] 5.2 Verificación manual: corrido contra la base de dev. De los 5 inmuebles existentes (seed + 1 manual), 2 quedaron geocodificados con Nominatim real (Calle 10 # 5-30, Avenida 80 # 34-21); 3 sin resultado por ser direcciones sintéticas no reales (quedan en `null`, reintentables re-corriendo el script — confirmado idempotente).

## 6. Frontend — toggle Lista/Mapa

- [x] 6.1 Agregar dependencias `leaflet` y `react-leaflet` a `frontend/inmuebles-app` (`package.json` del workspace). También `@types/leaflet` (dev) y ajustes de infraestructura de build necesarios: `transformIgnorePatterns` de Jest (react-leaflet/@react-leaflet/core son ESM-only), regla `asset/resource` en `rspack.config.ts` para los íconos PNG de Leaflet, y sus mocks/declaraciones equivalentes para Jest/TypeScript.
- [x] 6.2 (Red) Test (Jest + RTL): el listado público muestra el tab "Lista" seleccionado por defecto y un tab "Mapa" disponible.
- [x] 6.3 (Green) Agregar el control de tabs al componente contenedor del listado público existente (HU-003), sin duplicar la llamada a `inmuebles.api.ts` (ambas vistas comparten los mismos datos ya obtenidos).
- [x] 6.4 (Red) Test: al seleccionar "Mapa" se renderiza el componente de mapa; al volver a "Lista" se mantiene el listado original.
- [x] 6.5 (Green) Implementar el cambio de vista (estado local, sin nueva ruta).

## 7. Frontend — componente de mapa

- [x] 7.1 (Red→verificado) Test: con inmuebles que tienen coordenadas y otros que no, el mapa renderiza un marcador solo por cada uno con coordenadas. (`react-leaflet` mockeado — ver docstring de `InmueblesMap.test.tsx`: renderizar Leaflet real necesita layout de DOM real que jsdom no provee y no es la lógica propia de este componente).
- [x] 7.2 (Green) Implementar el componente de mapa con `react-leaflet` (`MapContainer`, `TileLayer` con tiles de OpenStreetMap, `Marker` por inmueble con coordenadas). Construido junto con 6.3 por el acoplamiento con el toggle; verificado retroactivamente con la suite de 7.1-7.7, todas en verde.
- [x] 7.3 (Red→verificado) Test: sin ningún inmueble con coordenadas, el mapa se renderiza vacío sin error.
- [x] 7.4 (Red→verificado) Test: el mapa se centra usando Medellín o el centro geográfico (promedio) de los inmuebles con coordenadas disponibles.
- [x] 7.5 (Green) Calcular el centro/bounds por defecto a partir de los inmuebles con coordenadas (fallback a coordenadas de Medellín si no hay ninguno) — `calcularCentro()`.
- [x] 7.6 (Red→verificado) Test: el popup de un marcador muestra foto principal + valor mensual + acción "Ver detalle" que invoca `onVerDetalle(id)`.
- [x] 7.7 (Green) Implementar el popup del marcador reutilizando los datos ya presentes en el listado (sin request adicional) y el callback `onVerDetalle` ya existente de HU-003 (mismo patrón router-agnóstico, design.md decisión 5 de hu-003).

## 8. Verificación end-to-end y documentación

- [x] 8.1 Escenario E2E: no hay Playwright configurado en el repo (sin `playwright.config.*` ni tests `.e2e.*` precedentes) — se verificó en vivo con el Playwright MCP contra `docker compose` real: listado público → tab "Mapa" (2 pines reales en Medellín, geocodificados por el backfill) → click en marcador → popup con foto real + precio + "Ver detalle" → navega al detalle correcto. Sin errores/warnings en consola.
- [x] 8.2 Suite completa: backend 403/403 tests (pytest), frontend 132/132 tests (Jest). Cobertura: `inmuebles/domain/inmueble.py` 100%, `inmuebles/domain/ports.py` 100%, `publicar_inmueble.py` 100%, `editar_inmueble.py` 95%, `nominatim_adapter.py`/`geocoding_fake_adapter.py`/`proveedor.py` 100%; frontend `InmueblesMap.tsx` 100%, `BusquedaPublicaPage.tsx` 90%, `inmuebles.api.ts` 97%.
- [x] 8.3 Verificación manual: ver 8.1 — el mismo recorrido en el navegador real confirma geocodificación y visualización en el mapa del listado público (no se probó publicar un inmueble nuevo dentro de esta sesión de verificación porque el backfill de 8.1/HU-005 ya deja 2 inmuebles reales geocodificados visibles; el camino de publicación nueva es exactamente el mismo código ya cubierto por los tests de `publicar_inmueble`, grupo 3).
- [x] 8.4 `docs/user-stories/HU-010-vista-mapa-inmuebles-leaflet.md` actualizado con los criterios de aceptación cumplidos.
