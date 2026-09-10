## Context

El listado público de inmuebles (HU-003, `frontend/inmuebles-app`, endpoints `GET /inmuebles/publicos` y `GET /inmuebles/publicos/{id}`) solo ofrece vista de lista. El agregado `Inmueble` (`backend/inmuebles/domain/inmueble.py`) no tiene coordenadas geográficas — solo `direccion`, `barrio` y `ciudad` como texto libre — así que no hay forma de ubicar los inmuebles en un mapa hoy.

El proyecto ya tiene tres integraciones con proveedores externos consolidadas como precedente directo: `identidad` → Truora (`TruoraAdapter`), `pagos` → Wompi, `seguro_arrendamiento` → Sura. Las tres siguen el mismo molde: un `Protocol` en `domain/ports.py`, un adaptador real con `httpx.AsyncClient` (timeout 10s) en `infrastructure/adapters/`, un `fake_adapter.py` para tests, y una llamada síncrona dentro del request que, si falla, lanza una excepción de dominio y corta el flujo de negocio.

Este change reutiliza esa misma forma para la geocodificación, con una diferencia deliberada: **el fallo no bloquea**, porque el mapa es una funcionalidad secundaria y el negocio (publicar un inmueble) no depende de tener coordenadas.

No existe en el proyecto ninguna infraestructura de background jobs (sin Celery, sin colas, sin uso de `BackgroundTasks` de FastAPI en ningún dominio existente) — se decidió explícitamente no introducir una para este change (ver Decisión 2).

## Goals / Non-Goals

**Goals:**
- Agregar `latitud`/`longitud` (nullable) a `Inmueble`, pobladas por geocodificación automática de la dirección al publicar/editar.
- Exponer esas coordenadas en `GET /inmuebles/publicos`.
- Agregar un tab "Mapa" (Leaflet + OpenStreetMap) al listado público existente, con marcadores navegables al detalle.
- Backfill único de los inmuebles ya publicados que no tengan coordenadas.

**Non-Goals:**
- Reintentos automáticos de geocodificación ante un fallo.
- Manejo especial del rate limit de Nominatim (colas, semáforos, backoff) — se acepta el riesgo en esta iteración.
- Clustering de marcadores, filtros geográficos (dibujar polígono), o geolocalización del usuario ("cerca de mí").
- Migrar de Nominatim a un proveedor comercial (Google/Mapbox/LocationIQ) — queda como posible iteración futura si el volumen lo justifica.
- Cambiar el formulario de publicación/edición (HU-001/HU-002): no se agrega ningún campo visible de ubicación; la geocodificación es invisible para quien publica.

## Decisions

### Decisión 1 — Geocodificación síncrona dentro del request de publicar/editar
Se geocodifica dentro del mismo request HTTP, antes de persistir, replicando el patrón de `TruoraAdapter`/Wompi/Sura.

**Alternativas consideradas:**
- *Background job (`BackgroundTasks` o cola dedicada):* el request de publicar respondería de inmediato sin esperar a Nominatim, y algo geocodificaría después. Se descartó porque el proyecto no tiene ninguna infraestructura de background jobs hoy, y `BackgroundTasks` in-process no sobrevive un reinicio del proceso a mitad de tarea (sin reintento, la pérdida sería silenciosa) — es una pieza de infraestructura nueva para un beneficio (evitar 1-2s de latencia en un flujo que ya sube fotos a S3 y puede tardar varios segundos) que no se consideró suficiente en esta etapa.
- *Geocodificación perezosa en la lectura (`GET /inmuebles/publicos`):* geocodificar la primera vez que se pide el listado/mapa, cacheando el resultado. Se descartó por decisión explícita del usuario a favor de mantener el mismo patrón síncrono ya usado en el resto del dominio, priorizando consistencia arquitectónica sobre desacoplar la latencia.

**Consecuencia aceptada:** publicar o editar un inmueble (cuando cambia su ubicación) ahora depende de la disponibilidad y latencia de Nominatim, un servicio público sin SLA.

### Decisión 2 — Sin manejo especial del rate limit de Nominatim
Nominatim limita a 1 request/segundo por IP de origen — y todas las publicaciones de la plataforma salen de la IP del backend, compartida entre todos los usuarios. No se introduce semáforo, cola ni cambio de proveedor en esta iteración.

**Alternativas consideradas:**
- *Serializar las llamadas con un lock/semáforo en el adaptador:* evita romper la política de uso de Nominatim, a costa de encolar publicaciones concurrentes (latencia adicional impredecible bajo carga).
- *Cambiar a un proveedor con mejor SLA (Google Geocoding, Mapbox, LocationIQ):* elimina el problema de raíz, pero introduce costo y gestión de API key para un volumen de publicaciones que hoy es mínimo (proyecto unipersonal, sin usuarios reales).

**Consecuencia aceptada:** riesgo de recibir un 429 ocasional de Nominatim bajo picos de publicaciones concurrentes — tratado igual que cualquier otro fallo de geocodificación (no bloquea, guarda `null`). Revisar esta decisión si el volumen de publicaciones crece.

### Decisión 3 — Re-geocodificar en edición solo si cambió la ubicación
`editar_inmueble` compara `direccion`/`barrio`/`ciudad` recibidos contra los valores actuales del inmueble antes de decidir si invoca `GeocodingPort`. Si ninguno cambió, conserva `latitud`/`longitud` existentes sin llamar a Nominatim.

**Alternativa considerada:** geocodificar siempre en cada edición, sin comparar. Se descartó por ser un gasto innecesario de tráfico hacia un servicio con rate limit compartido, para ediciones que típicamente cambian precio o descripción, no ubicación.

### Decisión 4 — `GeocodingPort` como Protocol nuevo en `inmuebles/domain/ports.py`
Se agrega un cuarto puerto junto a `InmuebleRepositoryPort` y `StoragePort`, siguiendo el mismo patrón estructural (`Protocol`, sin herencia de una base común). El adaptador real (`NominatimAdapter`) vive en `inmuebles/infrastructure/external/` (junto a `s3_storage_adapter.py`); un `fake_adapter.py` provee un doble determinístico para tests, replicando la convención de `identidad`/`pagos`/`seguro_arrendamiento`.

```python
class GeocodingPort(Protocol):
    async def geocodificar(
        self, *, direccion: str, barrio: str, ciudad: str
    ) -> Coordenadas | None:
        """Return coordinates for the given address, or None if not found /
        the provider failed. Never raises for a "not found" or provider
        error — those are expressed as `None`, not as an exception, so the
        use case never needs a try/except around this call."""
        ...
```

**Decisión de contrato explícita:** a diferencia de `TruoraAdapter.validar` (que lanza `ValidacionNoDisponible` en fallo, cortando el flujo), `NominatimAdapter.geocodificar` **no lanza** ante timeout/error/sin-resultado — devuelve `None`. Esto empuja la semántica de "no bloqueante" al contrato del puerto en vez de a un try/except disperso en cada caller (`publicar_inmueble` y `editar_inmueble`), evitando que un futuro tercer caller olvide envolver la llamada.

### Decisión 5 — Migración de columnas nullable + backfill como script standalone
`latitud`/`longitud` (`Numeric`, nullable) se agregan a la tabla `inmueble` vía una migración Alembic estándar (siguiendo el patrón de las migraciones recientes en `backend/alembic/versions/`). El backfill de inmuebles existentes sin coordenadas se implementa como un script Python standalone (mismo estilo que `scripts/seed_data.py`: idempotente, ejecutable con `docker compose exec backend`), no como parte de la migración de Alembic — así una migración de esquema nunca depende de una llamada de red a un servicio externo, que podría fallar o tardar y dejar la migración en un estado incierto.

### Decisión 6 — Frontend: `react-leaflet` dentro de `inmuebles-app`
El toggle Lista/Mapa y el componente de mapa se agregan al mismo microfrontend `inmuebles-app` que ya implementa el listado/detalle público de HU-003, reutilizando `inmuebles.api.ts`. Se usa `react-leaflet` como wrapper de Leaflet para integración idiomática con React (hooks, componentes declarativos `<MapContainer>`/`<Marker>`) en vez de manipular la instancia de Leaflet imperativamente.

## Flujo: publicar inmueble con geocodificación

```
Propietario/Agente          API (inmuebles)         GeocodingPort           InmuebleRepositoryPort
      │                          │                        │                          │
      │  POST /inmuebles         │                        │                          │
      │─────────────────────────▶│                        │                          │
      │                          │  geocodificar(dir,     │                          │
      │                          │  barrio, ciudad)       │                          │
      │                          │───────────────────────▶│                          │
      │                          │                        │  (llamada a Nominatim)   │
      │                          │   Coordenadas | None    │                          │
      │                          │◀───────────────────────│                          │
      │                          │  Inmueble.crear(..., lat, lng)                     │
      │                          │  guardar(inmueble)                                 │
      │                          │────────────────────────────────────────────────────▶│
      │                          │                        │            Inmueble       │
      │                          │◀────────────────────────────────────────────────────│
      │   201 Created            │                        │                          │
      │◀─────────────────────────│                        │                          │
```

No hay flujo de autenticación nuevo que diagramar: `publicar_inmueble`/`editar_inmueble` reutilizan la autorización ya existente de HU-001/HU-002/HU-008 sin cambios.

## Estrategia de testing

- **`GeocodingPort`/`NominatimAdapter`** (backend, pytest): tests unitarios del adaptador real contra un mock de `httpx.AsyncClient` (patrón ya usado para `TruoraAdapter`) cubriendo: respuesta exitosa, timeout, error 4xx/5xx, y respuesta vacía (sin resultados) — las cuatro deben devolver `None` en los tres últimos casos, nunca lanzar. `fake_adapter.py` se cubre con un test trivial de que devuelve lo configurado.
- **`publicar_inmueble` / `editar_inmueble`** (backend, pytest, TDD Red-Green-Refactor): tests con el `fake_adapter` inyectado vía el puerto, cubriendo: geocodificación exitosa persiste coordenadas; `GeocodingPort` devuelve `None` y el inmueble se crea igual con `latitud`/`longitud` en `null`; edición que cambia `direccion` invoca el puerto; edición que no toca ubicación NO invoca el puerto (se verifica con un spy/mock de llamadas).
- **`GET /inmuebles/publicos`** (backend, pytest): test de que el DTO de respuesta incluye `latitud`/`longitud`, incluyendo el caso `null`.
- **Migración Alembic**: test de que `upgrade`/`downgrade` corren limpio contra la base de test (patrón ya seguido por migraciones anteriores del proyecto).
- **Script de backfill**: test manual documentado en `tasks.md` (correr contra la base de dev con `docker compose exec backend`, igual que se validó `seed_data.py`) — no forma parte de la suite de pytest, siguiendo el precedente de `scripts/seed_data.py`, que tampoco tiene test automatizado.
- **Frontend (`inmuebles-app`)**: Jest + React Testing Library para el toggle Lista/Mapa (estado por defecto, cambio de tab) y para el componente de mapa (marcadores solo para inmuebles con coordenadas, mapa vacío si ninguno tiene, popup con foto/valor/link al hacer click en un marcador — mockeando `react-leaflet`). Cobertura E2E (Playwright) del flujo completo: abrir listado público → cambiar a tab Mapa → click en marcador → llegar al detalle.

## Risks / Trade-offs

- **[Riesgo] Nominatim sin SLA acopla la latencia/disponibilidad de "publicar inmueble" (HU-001, la funcionalidad más crítica del MVP) a un servicio público de terceros.** → Mitigación: fallo nunca bloquea (Decisión 4); si en producción se vuelve un problema recurrente, la Decisión 1 puede revisarse sin tocar el dominio (el `GeocodingPort` ya aísla el proveedor).
- **[Riesgo] Rate limit de 1 req/seg compartido por IP puede generar 429s bajo picos de publicaciones concurrentes.** → Mitigación: aceptado explícitamente para el volumen actual (Decisión 2); se trata como cualquier fallo de geocodificación (no bloquea). Punto de revisión futuro si crece el volumen.
- **[Riesgo] El script de backfill puede quedar desactualizado si se agregan más tablas relacionadas a `Inmueble` en el futuro (mismo problema que ya ocurrió con `scripts/seed_data.py` y las tablas de `identidad`/`firma_contrato`/`pagos`/`seguro_arrendamiento`).** → Mitigación: el backfill solo lee y actualiza `inmueble.latitud`/`longitud` por id — no borra ni recrea filas, así que no depende de conocer FKs de otras tablas como sí le pasaba a la limpieza de `seed_data.py`.
- **[Trade-off] Geocodificar solo al publicar/editar (Decisión 1) implica que inmuebles nunca editados después de este change no tendrán coordenadas hasta el backfill de despliegue.** → Mitigación: el backfill único cubre exactamente ese caso (Decisión 5).

## Migration Plan

1. Migración Alembic: agregar `latitud`, `longitud` (`Numeric`, nullable) a la tabla `inmueble`. Reversible (`downgrade` elimina las columnas) sin pérdida de datos existentes (son columnas nuevas).
2. Desplegar el código del backend (dominio + adaptador + endpoints actualizados). Sin esto, el paso 1 ya es seguro por sí solo (columnas nullable no rompen nada).
3. Correr el script de backfill una vez contra la base de producción (`docker compose exec backend ...`, mismo mecanismo que `seed_data.py`), geocodificando los inmuebles existentes sin coordenadas.
4. Desplegar el frontend (`inmuebles-app`) con el tab de mapa.

**Rollback:**
- Frontend: ocultar el tab "Mapa" (o revertir el deploy de `inmuebles-app`) sin tocar el backend — el listado en modo lista sigue funcionando exactamente igual que antes de este change.
- Backend: si la geocodificación causa problemas (latencia, errores inesperados), se puede desactivar la invocación a `GeocodingPort` en `publicar_inmueble`/`editar_inmueble` (queda como no-op) sin revertir la migración — el inmueble se sigue publicando/editando normalmente, solo sin coordenadas nuevas.
- Solo si se abandona la funcionalidad por completo: revertir la migración (`alembic downgrade`) para eliminar `latitud`/`longitud`. No es necesario para un rollback parcial.

## Open Questions

- Ninguna pendiente de decisión de producto — todas las decisiones relevantes se cerraron durante `/opsx:explore` (timing síncrono, manejo de rate limit, regla de re-geocodificación en edición, backfill único, empaquetado en un solo change) y quedaron reflejadas en las Decisiones 1-6 de este documento.
- Pendiente técnico menor a resolver durante implementación (no bloquea el diseño): el formato exacto de la query a Nominatim (`q=` de texto libre vs. parámetros estructurados `street`/`city`) y el header `User-Agent` a enviar (requerido por la política de uso de Nominatim) — se decide al escribir `NominatimAdapter`, no cambia ningún contrato de dominio.
