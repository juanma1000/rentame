## 1. Backend — exponer coordenadas en el detalle público

- [x] 1.1 (Red) Test en `tests/inmuebles/infrastructure/test_api.py` (clase `TestGetInmueblePublicoDetalle`): `GET /inmuebles/publicos/{id}` de un inmueble con coordenadas devuelve `latitud`/`longitud` en el body.
- [x] 1.2 (Red) Test: `GET /inmuebles/publicos/{id}` de un inmueble sin coordenadas devuelve `latitud`/`longitud` en `null`.
- [x] 1.3 (Green) Agregar `latitud: float | None` y `longitud: float | None` a `InmueblePublicoResponse` (`infrastructure/api/schemas.py`) y a su `from_domain`, siguiendo el mismo patrón ya usado en `InmueblePublicoListItemResponse` (HU-010).
- [x] 1.4 Correr la suite completa de `inmuebles` (pytest): 105/105 en verde.

## 2. Frontend — tipos y mapper

- [x] 2.1 (Red) Test en `services/__tests__/inmuebles.api.test.ts`: `obtenerPublico` mapea `latitud`/`longitud` (snake_case → camelCase) desde la respuesta raw, incluyendo el caso `null`.
- [x] 2.2 (Green) Agregar `latitud: number | null` y `longitud: number | null` a `InmueblePublicoDetalle` y a `RawInmueblePublicoDetalleApi` (`services/inmuebles.api.ts`), y mapearlos en `mapInmueblePublicoDetalleFromApi`. También actualizados los fixtures tipados en `BusquedaPublicaRoutes.test.tsx` e `InmuebleDetallePublicoPage.test.tsx` que quedaron sin compilar por el tipo ampliado.

## 3. Frontend — componente de mini mapa

- [x] 3.1 (Red) Test nuevo (`components/__tests__/InmuebleMiniMapa.test.tsx`, mockeando `react-leaflet` igual que `InmueblesMap.test.tsx`): con coordenadas dadas, renderiza un único marcador centrado en esas coordenadas.
- [x] 3.2 (Red) Test: el `MapContainer` mockeado recibe `scrollWheelZoom={false}`.
- [x] 3.3 (Red) Test: el `MapContainer` mockeado recibe un `zoom` más alto (más cercano) que `DEFAULT_ZOOM` de `InmueblesMap` (nivel de calle, ej. 16).
- [x] 3.4 (Green) Crear `components/InmuebleMiniMapa.tsx`: recibe `latitud`/`longitud`, renderiza `MapContainer` + `TileLayer` (mismos tiles OSM que `InmueblesMap`) + un único `Marker` con `defaultMarkerIcon` (reutilizado de `components/leafletIcon.ts`), sin `Popup`. No calcula centro promedio (a diferencia de `InmueblesMap`): el centro es directamente `[latitud, longitud]`. Zoom por defecto 16.

## 4. Frontend — integración en la página de detalle

- [x] 4.1 (Red) Test en `pages/__tests__/InmuebleDetallePublicoPage.test.tsx` (mockeando `InmuebleMiniMapa` igual que `BusquedaPublicaPage.test.tsx` mockea `InmueblesMap`): con un fixture de detalle que tiene `latitud`/`longitud`, se renderiza el mini mapa con esas coordenadas.
- [x] 4.2 (Red) Test: con un fixture de detalle con `latitud`/`longitud` en `null`, el mini mapa NO se renderiza (sin placeholder, sin error).
- [x] 4.3 (Green) Integrar `InmuebleMiniMapa` en `InmuebleDetallePublicoPage.tsx`: renderizado condicional (`detalle.latitud !== null && detalle.longitud !== null`), ubicado después del párrafo de barrio/ciudad.

## 5. Verificación

- [x] 5.1 Backend 405/405 (pytest), frontend 138/138 (Jest). Cobertura: `schemas.py` 94%, `InmuebleMiniMapa.tsx` 100%, `InmuebleDetallePublicoPage.tsx` 88%, `inmuebles.api.ts` 97% — todas por encima del 80%.
- [x] 5.2 `tsc --noEmit` y `eslint` limpios; `mypy` limpio; `ruff check` limpio salvo un error preexistente en `test_api.py:615` no relacionado a este change (línea ya existente antes de HU-010).
- [x] 5.3 Verificación manual (Playwright MCP, `docker compose` local): "Calle 10 # 5-30" (geocodificado) muestra el mini mapa centrado en El Poblado, zoom 16; scroll del mouse sobre él movió la página (`scrollY` 0→16) y los tiles pedidos siguieron todos en zoom `/16/` (sin cambio de zoom); "Carrera 45 # 12-08" (sin coordenadas) no muestra ninguna sección de mapa, sin errores/warnings en consola.
- [x] 5.4 No aplica: este change no tiene una HU propia en `docs/user-stories/` — es un refinamiento técnico directo de HU-010 (gap de un endpoint que quedó sin coordenadas), propuesto vía `/opsx:explore` + `/opsx:propose` sin pasar por la skill de nueva historia de usuario.
