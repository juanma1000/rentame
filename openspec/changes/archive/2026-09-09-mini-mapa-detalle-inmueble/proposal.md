## Why

Desde HU-010 (`vista-mapa-inmuebles-leaflet`), el listado público de inmuebles ya tiene un mapa agregado con todos los inmuebles disponibles, pero la página de **detalle** de un inmueble puntual no muestra dónde queda — un inquilino que ya entró al detalle solo ve texto (barrio, ciudad) y tiene que volver al listado y buscar el pin correspondiente para ubicarlo en el mapa. Cada inmueble ya tiene sus coordenadas geocodificadas desde HU-010; falta exponerlas y mostrarlas en el propio detalle.

## What Changes

- El endpoint `GET /inmuebles/publicos/{id}` (`InmueblePublicoResponse`) expone `latitud`/`longitud` (nullable) — hoy solo el listado (`GET /inmuebles/publicos`) las expone, no el detalle.
- La página de detalle (`InmuebleDetallePublicoPage`, `frontend/inmuebles-app`) muestra un mini mapa Leaflet con un único marcador en la ubicación del inmueble, cuando tiene coordenadas.
  - Componente nuevo y dedicado (no se reutiliza `InmueblesMap` de HU-010, que asume múltiples inmuebles y un popup "Ver detalle" — redundante en una página donde ya se está viendo ese detalle).
  - `scrollWheelZoom` deshabilitado: el scroll del mouse sobre el mini mapa siempre mueve la página, nunca hace zoom (decisión distinta a la del mapa agregado, que sí tiene scroll-zoom porque el usuario entra a esa vista a propósito a interactuar con el mapa).
  - Zoom por defecto más cercano que el del mapa agregado (nivel de calle), ya que centra en un único punto conocido, no en un conjunto de inmuebles dispersos.
  - Sin marcador ni acción de navegación en el mini mapa (no hace falta un "Ver detalle": ya se está ahí).
- Si el inmueble no tiene coordenadas (geocodificación fallida o inmueble publicado antes de HU-010 y aún no editado/backfillado), la sección del mini mapa no se muestra — mismo criterio de "ausencia silenciosa, nunca error" que ya rige el mapa agregado.

## Capabilities

### New Capabilities
(ninguna)

### Modified Capabilities
- `inmuebles`: el requirement "Detalle público de un inmueble disponible" (`GET /inmuebles/publicos/{id}`) gana `latitud`/`longitud` (nullable) en la respuesta.
- `inmuebles-mapa-ui`: se agrega un nuevo requirement ("Mini mapa en el detalle del inmueble") a la capacidad ya existente de HU-010 — misma capacidad temática (visualización en mapa de inmuebles vía Leaflet/OSM), ahora también en la página de detalle además del listado agregado.

## Impact

- **Backend** (`backend/inmuebles/infrastructure/api/schemas.py`): agregar `latitud`/`longitud` a `InmueblePublicoResponse.from_domain`. Ningún cambio en dominio, aplicación ni persistencia (los campos ya existen en `Inmueble` desde HU-010).
- **Frontend** (`frontend/inmuebles-app`): nuevo componente de mini mapa de un solo punto; `InmueblePublicoDetalle`/mapper en `services/inmuebles.api.ts` gana `latitud`/`longitud`; `InmuebleDetallePublicoPage` lo renderiza condicionalmente.
- **Equipos/microfrontends afectados:** `backend` (dominio `inmuebles`, solo capa API) e `inmuebles-app` (único microfrontend de frontend afectado).
- **Sin dependencias externas nuevas:** reutiliza Leaflet/`react-leaflet`/tiles de OpenStreetMap ya integrados en HU-010, y el fix de íconos (`leafletIcon.ts`) ya existente.
- **Plan de rollback:** cambio aditivo y no destructivo. El campo nuevo en `InmueblePublicoResponse` es nullable y no rompe ningún consumidor existente. Si el mini mapa da problemas en producción, se puede ocultar solo en el frontend (revertir el deploy de `inmuebles-app`, o remover el componente de `InmuebleDetallePublicoPage`) sin tocar el backend — la respuesta ampliada del detalle es inocua para cualquier cliente que no la lea.
