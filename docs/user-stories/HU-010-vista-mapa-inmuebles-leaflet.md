# HU-010 — Vista de mapa de inmuebles con Leaflet

## Historia
Como inquilino,
quiero alternar entre una vista de lista y una vista de mapa al buscar inmuebles disponibles,
para ubicar geográficamente las opciones y decidir más rápido cuáles me convienen por zona.

## Criterios de aceptación
- [x] El listado público de inmuebles (`/`) muestra un control tipo tab/toggle para alternar entre "Lista" y "Mapa".
- [x] La vista de mapa usa Leaflet con tiles de OpenStreetMap (sin costo de licencia).
- [x] El universo de inmuebles mostrado en el mapa es el mismo que hoy devuelve `GET /inmuebles/publicos` (inmuebles con estado "Disponible"), sin filtros adicionales propios del mapa.
- [x] Al publicar o editar un inmueble (HU-001/HU-002), el sistema geocodifica automáticamente su dirección/barrio/ciudad y guarda `latitud`/`longitud` sin intervención del propietario o agente (sin campo nuevo en el formulario).
- [x] Si la geocodificación automática falla o no encuentra resultado, el inmueble se publica igual (sin coordenadas) — la falla de geocodificación nunca bloquea la publicación.
- [x] Cada inmueble disponible que tenga coordenadas (obtenidas por geocodificación automática) se pinta como un marcador en el mapa.
- [x] Un inmueble sin coordenadas (geocodificación fallida o no ejecutada) simplemente no se pinta en el mapa — su ausencia no genera error ni rompe la carga de la vista.
- [x] Al hacer click/tap sobre un marcador se muestra al menos foto principal, valor mensual y un enlace/acción para ir al detalle del inmueble (mismo detalle ya implementado en HU-003).
- [x] Si ningún inmueble tiene coordenadas, la vista de mapa se muestra vacía (mapa renderizado sin marcadores), no rota ni se oculta el tab.
- [x] El mapa se centra por defecto en Medellín (o en el centro geográfico de los inmuebles con coordenadas disponibles, a criterio de implementación).
- [x] La vista de lista (HU-003) permanece como vista por defecto; el mapa es una alternativa, no reemplaza la lista.

## Notas técnicas
- **Gap de dominio detectado (bloqueante):** el modelo `Inmueble` hoy NO tiene campos de latitud/longitud — solo dirección, barrio y ciudad como texto libre (ver nota técnica de HU-003). Esta HU no puede completarse sin resolver esto primero. Decisión confirmada por el usuario: ampliar el modelo `Inmueble` con campos opcionales `latitud`/`longitud` como parte del alcance de esta misma HU (no como HU separada), poblados mediante **geocodificación automática** de `direccion` + `barrio` + `ciudad` al momento de publicar (HU-001/HU-002) o editar el inmueble — sin captura ni ajuste manual en v1.
- **Proveedor de geocodificación (v1):** Nominatim (API pública de OpenStreetMap), por consistencia con Leaflet/OSM ya elegido para los tiles del mapa y por no requerir API key ni costo para el volumen esperado en esta etapa. Restricciones a respetar: máximo 1 request/segundo, header `User-Agent` identificando la aplicación, y no debe usarse para autocompletado en vivo (solo geocodificación puntual al guardar). Queda como punto abierto para una iteración futura migrar a un proveedor con SLA/rate limit mayor si el volumen de publicaciones lo justifica.
- **Manejo de fallos de geocodificación:** si Nominatim no encuentra coordenadas para la dirección dada (dirección ambigua, mal escrita, o el servicio no responde), la publicación del inmueble **no se bloquea** — se guarda con `latitud`/`longitud` en `null` y el inmueble simplemente no aparece en la vista de mapa (sí en la lista). No hay reintento automático ni notificación al propietario/agente en v1.
- Frontend: se implementa en `frontend/inmuebles-app` (mismo microfrontend de HU-003, vía Module Federation), reutilizando `inmuebles.api.ts` y el listado ya existente. El toggle Lista/Mapa vive en el mismo componente contenedor del listado público. El formulario de publicación (HU-001/HU-002) no cambia su UI — no se agrega ningún campo ni mini-mapa manual.
- Backend: se agrega un servicio de geocodificación (adaptador de infraestructura en el dominio `inmuebles`) invocado de forma síncrona al crear/actualizar un inmueble, antes de persistir. No se anticipan nuevos endpoints públicos — se reutiliza `GET /inmuebles/publicos`, ampliando el DTO de respuesta para incluir `latitud`/`longitud` (nullable) por inmueble.
- Librería: Leaflet (open source, sin costo de licencia) + tiles de OpenStreetMap por defecto. Evaluar `react-leaflet` como wrapper para integración idiomática con React.
- Fuera de alcance de esta HU: clustering de marcadores, filtros geográficos (dibujar polígono de búsqueda), geolocalización del usuario ("cerca de mí"), reintento/backfill de geocodificación para inmuebles ya publicados antes de esta HU (esos quedan sin coordenadas hasta que se editen).

## Prioridad
Media

## Estimación
08 - Muy Grande (17h) — mayor que HU-003 (05, reducida a 2 endpoints read-only) porque además de reutilizar el listado hay que: ampliar el modelo de dominio con lat/lng, integrar un adaptador de geocodificación externo (Nominatim) en el flujo de publicación/edición de HU-001/HU-002 con manejo de fallos, integrar Leaflet/react-leaflet, construir el toggle de vistas y manejar el caso de inmuebles sin coordenadas.
