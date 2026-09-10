## Why

El listado público de inmuebles (HU-003) solo se puede recorrer en formato lista. Un inquilino que busca por zona no tiene forma de ubicar geográficamente las opciones disponibles sin leer cada dirección de texto una por una. Agregar una vista de mapa (Leaflet + OpenStreetMap) resuelve esto, pero requiere primero que `Inmueble` tenga coordenadas — hoy el dominio solo guarda dirección, barrio y ciudad como texto libre.

## What Changes

- Se agregan campos `latitud`/`longitud` (opcionales) al agregado `Inmueble`.
- Al publicar o editar un inmueble, el backend geocodifica automáticamente `direccion` + `barrio` + `ciudad` contra Nominatim (API pública de OpenStreetMap) y guarda las coordenadas resultantes — de forma síncrona, dentro del mismo request, siguiendo el mismo patrón que las integraciones externas ya existentes (Truora, Wompi, Sura).
  - En edición, solo se vuelve a geocodificar si cambió alguno de los tres campos de ubicación; si no cambiaron, se conservan las coordenadas existentes.
  - Si Nominatim falla, no responde o no encuentra resultado, la publicación/edición **no se bloquea**: el inmueble se guarda con `latitud`/`longitud` en `null` (comportamiento distinto al de Truora/Wompi/Sura, que sí bloquean su flujo ante un fallo del proveedor — aquí el mapa es una funcionalidad secundaria, no bloqueante del negocio).
  - No hay reintento automático ni manejo especial del rate limit de Nominatim (1 req/seg) en esta iteración — riesgo aceptado dado el volumen actual del proyecto.
- Script de backfill (estilo `scripts/seed_data.py`) que geocodifica una sola vez, al desplegar este cambio, los inmuebles ya publicados que no tengan coordenadas.
- `GET /inmuebles/publicos` expone `latitud`/`longitud` (nullable) en su respuesta.
- El listado público (`frontend/inmuebles-app`, HU-003) agrega un control tipo tab/toggle "Lista" / "Mapa"; la vista de mapa usa Leaflet (vía `react-leaflet`) con tiles de OpenStreetMap, pinta un marcador por cada inmueble disponible con coordenadas, omite silenciosamente los que no las tienen, y al hacer click en un marcador muestra foto principal, valor mensual y un enlace al detalle (mismo detalle ya implementado en HU-003).

## Capabilities

### New Capabilities
- `inmuebles-mapa-ui`: tab de vista de mapa (Leaflet/OpenStreetMap) en el listado público de inmuebles, con marcadores por inmueble disponible y navegación al detalle desde el marcador.

### Modified Capabilities
- `inmuebles`: los requerimientos "Creación de publicación de inmueble" y "Edición de inmueble publicado" ganan un paso de geocodificación automática no bloqueante; el requerimiento "Listado público de inmuebles disponibles" expone `latitud`/`longitud` en la respuesta.

## Impact

- **Backend** (`backend/inmuebles/`): nuevo puerto `GeocodingPort` (`domain/ports.py`), adaptador real `NominatimAdapter` + `fake_adapter.py` para tests (mismo patrón que `identidad`/`pagos`/`seguro_arrendamiento`), migración Alembic para las columnas nuevas, cambios en `domain/inmueble.py`, `application/publicar_inmueble.py`, `application/editar_inmueble.py`, `infrastructure/api/schemas.py` (DTO de `GET /inmuebles/publicos`), y `scripts/` (nuevo script de backfill).
- **Frontend** (`frontend/inmuebles-app`): nueva dependencia `leaflet` + `react-leaflet`, nuevo componente de vista de mapa, modificación del contenedor del listado público (HU-003) para agregar el toggle.
- **Equipos/microfrontends afectados:** `backend` (dominio `inmuebles`) y `inmuebles-app` (único microfrontend de frontend afectado — `shell` y `arrendamiento-app` no cambian).
- **Dependencia externa nueva:** Nominatim (`nominatim.openstreetmap.org`), servicio público sin costo ni API key, sujeto a su política de uso (1 req/seg, header `User-Agent` obligatorio).
- **Plan de rollback:** el cambio es aditivo y no destructivo — las columnas `latitud`/`longitud` son nullable y no alteran ningún comportamiento existente si se remueven. Si la geocodificación o el adaptador de Nominatim causan problemas en producción, se puede:
  1. Feature-flag/desactivar la llamada a `GeocodingPort` en `publicar_inmueble`/`editar_inmueble` (queda como no-op, todo sigue funcionando igual que hoy, solo sin coordenadas nuevas).
  2. Ocultar el tab de mapa en el frontend sin tocar el backend (los datos ya recolectados no se pierden).
  3. Revertir la migración de columnas solo si además se decide abandonar la funcionalidad por completo (no es necesario para un rollback parcial).
