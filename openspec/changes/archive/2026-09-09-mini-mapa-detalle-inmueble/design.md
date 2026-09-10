## Context

HU-010 (`vista-mapa-inmuebles-leaflet`, archivada en `openspec/changes/archive/2026-09-09-vista-mapa-inmuebles-leaflet/`) agregó `latitud`/`longitud` al agregado `Inmueble`, geocodificación automática al publicar/editar, y un mapa agregado (`InmueblesMap.tsx`) con un marcador por inmueble en el listado público (`GET /inmuebles/publicos`). Ese trabajo dejó dos piezas ya resueltas que este change reutiliza directamente sin tocarlas: el dominio (`Inmueble.latitud`/`longitud` ya existen y se pueblan solos) y la infraestructura Leaflet del frontend (`leaflet`/`react-leaflet` ya instalados, `leafletIcon.ts` ya resuelve el problema de los íconos de marcador bajo bundlers, `rspack.config.ts`/Jest ya configurados para assets PNG y módulos ESM-only).

Lo que falta es exclusivamente: (a) el endpoint de **detalle** (`GET /inmuebles/publicos/{id}` → `InmueblePublicoResponse`) nunca expuso `latitud`/`longitud` — solo el de listado lo hace — y (b) la página de detalle (`InmuebleDetallePublicoPage.tsx`) no muestra ningún mapa.

## Goals / Non-Goals

**Goals:**
- Exponer `latitud`/`longitud` (nullable) en `GET /inmuebles/publicos/{id}`.
- Mostrar un mini mapa de un solo punto en `InmuebleDetallePublicoPage` cuando el inmueble tenga coordenadas.
- El scroll del mouse sobre el mini mapa nunca debe interferir con el scroll de la página.

**Non-Goals:**
- Mini mapas en las cards del listado/grid (`BusquedaPublicaPage`) — fuera de alcance, ver Decisión 1.
- Cualquier cambio al dominio, geocodificación, backfill o al mapa agregado de HU-010 — ninguno de esos se toca.
- Activación de scroll-zoom con click/Ctrl (patrón "click para interactuar") — se descartó explícitamente en el explore por ser UI nueva no justificada para este alcance.

## Decisions

### Decisión 1 — Solo la página de detalle, no las cards del listado
El mini mapa se implementa únicamente en `InmuebleDetallePublicoPage`.

**Alternativa considerada:** un mini mapa por card en `BusquedaPublicaPage` (vista de lista). Se descartó porque implicaría renderizar tantas instancias de `MapContainer`/Leaflet en simultáneo como inmuebles haya en el grid (cada una con sus propios tiles, listeners y peso), un problema de rendimiento cualitativamente distinto al mapa agregado de HU-010 (una sola instancia con N marcadores). La página de detalle solo muestra un inmueble a la vez, así que esa preocupación no aplica ahí.

### Decisión 2 — Componente nuevo, no reutilizar `InmueblesMap`
Se crea un componente dedicado (`InmuebleMiniMapa` o nombre equivalente) en vez de reutilizar `InmueblesMap.tsx` de HU-010.

**Alternativa considerada:** pasarle a `InmueblesMap` una lista de un solo inmueble. Se descartó porque `InmueblesMap` fue diseñado para múltiples inmuebles: calcula un centro promedio entre varios (innecesario con uno solo — el centro es directamente sus coordenadas) y cada marcador abre un popup con foto + valor + botón "Ver detalle" (redundante: en el detalle ya se está viendo esa información y ya se está en esa página). Forzar ese componente a un solo punto sería adaptar una abstracción a un caso que no encaja, en vez of construir el componente pequeño que el caso realmente pide.

**Reuso real:** el fix de íconos (`components/leafletIcon.ts`, `defaultMarkerIcon`) sí se reutiliza tal cual — es genérico a cualquier marcador Leaflet del proyecto, no específico de `InmueblesMap`.

### Decisión 3 — `scrollWheelZoom` deshabilitado en el mini mapa
A diferencia del mapa agregado (`InmueblesMap`, que tiene `scrollWheelZoom` habilitado con `zoomSnap`/`zoomDelta` fraccionarios para un zoom suave — el usuario entra a ese tab a propósito a interactuar con el mapa), el mini mapa del detalle vive embebido dentro de una página que el usuario probablemente está scrolleando de principio a fin (fotos, precio, descripción). Con `scrollWheelZoom` activo, pasar el mouse por encima del mini mapa mientras se scrollea la página secuestraría el scroll para hacer zoom en su lugar — una fricción de UX real y ya discutida explícitamente con el usuario en el explore previo.

**Alternativas consideradas:**
- Scroll-zoom habitado igual que el mapa agregado: descartada por la razón anterior.
- Patrón "click para activar" (overlay "Click para interactuar", común en mapas embebidos de terceros como Google Maps): descartada por ser UI adicional no existente hoy en el proyecto, para un beneficio marginal en esta página (el usuario igual puede hacer zoom con los botones +/- o pellizcando en mobile).

**Consecuencia aceptada:** un usuario que quiera hacer zoom en el mini mapa debe usar los controles +/- (o pellizcar en mobile), nunca el scroll del mouse.

### Decisión 4 — Zoom por defecto más cercano que el mapa agregado
El mini mapa centra con un nivel de zoom más alto (más cercano, nivel de calle — ej. 16) que el mapa agregado (`DEFAULT_ZOOM = 12` en `InmueblesMap.tsx`, pensado para mostrar varios inmuebles dispersos por Medellín). Acá el punto de interés es uno solo y conocido, así que conviene mostrar el detalle del entorno inmediato (la cuadra, el barrio) en vez de la ciudad completa.

### Decisión 5 — Sin coordenadas, sin sección (silenciosa)
Igual que el mapa agregado omite un inmueble sin coordenadas del conjunto de marcadores, la página de detalle omite toda la sección del mini mapa (ningún placeholder, ningún mensaje de "ubicación no disponible") cuando `latitud`/`longitud` son `null`. Consistencia con el principio ya establecido en HU-010: la ausencia de coordenadas nunca es un error visible.

## Sequence — carga del detalle con mini mapa

No hay flujo de autenticación nuevo que diagramar (`GET /inmuebles/publicos/{id}` ya es público, sin cambios de autorización). El único flujo relevante es el fetch ya existente, ahora con un campo más en la respuesta:

```
Persona (sin sesión)      InmuebleDetallePublicoPage        API pública
      │                          │                              │
      │  abre /inmuebles/{id}    │                              │
      │─────────────────────────▶│                              │
      │                          │  GET /inmuebles/publicos/{id}│
      │                          │─────────────────────────────▶│
      │                          │   { ...detalle, latitud,     │
      │                          │     longitud }                │
      │                          │◀─────────────────────────────│
      │                          │                              │
      │                          │  latitud/longitud != null?    │
      │                          │  ├─ sí → renderiza mini mapa   │
      │                          │  └─ no → omite la sección     │
      │   página completa        │                              │
      │◀─────────────────────────│                              │
```

## Estrategia de testing

- **Backend** (`GET /inmuebles/publicos/{id}`, pytest): test de que `InmueblePublicoResponse` incluye `latitud`/`longitud`, con el caso `null` explícito (mismo patrón ya usado para `GET /inmuebles/publicos` en HU-010, `test_api.py`).
- **`InmueblePublicoDetalle`/mapper** (`inmuebles.api.ts`, Jest): test de que `obtenerPublico` mapea `latitud`/`longitud` snake_case → camelCase, incluyendo `null`.
- **Componente de mini mapa** (Jest + RTL): mismo enfoque que `InmueblesMap.test.tsx` de HU-010 — mockear `react-leaflet` por completo (no depende de layout real de Leaflet bajo jsdom) y verificar: se renderiza un único marcador en las coordenadas dadas; `scrollWheelZoom` se pasa en `false` al `MapContainer` mockeado; con coordenadas `null` el componente no renderiza nada (o el padre no lo monta, según cómo quede la composición).
- **`InmuebleDetallePublicoPage`** (Jest + RTL): test de que el mini mapa se muestra cuando el fixture de detalle trae coordenadas, y no se muestra cuando vienen en `null` — mockeando el componente de mini mapa igual que `BusquedaPublicaPage.test.tsx` mockea `InmueblesMap` hoy.
- **Verificación manual**: en `docker compose` local, abrir el detalle de un inmueble ya geocodificado (de los que quedaron con coordenadas tras el backfill de HU-010) y confirmar visualmente el mini mapa y que el scroll del mouse sobre él mueve la página.

## Risks / Trade-offs

- **[Riesgo] Duplicar sutilmente lógica de Leaflet entre `InmueblesMap` y el nuevo componente (import de `leaflet/dist/leaflet.css`, `TileLayer` con la misma URL/atribución de OSM).** → Mitigación: se acepta esta pequeña duplicación en vez de forzar una abstracción compartida prematura entre dos componentes con propósitos y formas distintas (uno para N puntos con navegación, otro para 1 punto sin ella) — revisar si aparece un tercer caso antes de extraer un helper común.
- **[Trade-off] Sin scroll-zoom en el mini mapa, el usuario pierde el gesto más natural de zoom (rueda del mouse) en esa vista puntual.** → Aceptado explícitamente (Decisión 3): prioriza no romper el scroll de la página por sobre la comodidad de zoom con rueda en un mapa que es secundario en esa pantalla.

## Migration Plan

1. Backend: agregar `latitud`/`longitud` a `InmueblePublicoResponse.from_domain` — cambio aditivo, no rompe ningún cliente existente que ignore el campo nuevo.
2. Frontend: agregar los campos al tipo/mapper de `InmueblePublicoDetalle`, construir el componente de mini mapa, integrarlo en `InmuebleDetallePublicoPage`.
3. Desplegar backend y frontend (orden indistinto — el campo nuevo es aditivo en ambos lados).

**Rollback:** revertir el deploy de `inmuebles-app` (o remover el componente de `InmuebleDetallePublicoPage`) sin tocar el backend — la respuesta ampliada del detalle es inocua para cualquier cliente. No hace falta revertir el cambio de backend salvo que se decida abandonar la funcionalidad por completo.

## Open Questions

Ninguna pendiente de decisión de producto — todas las decisiones relevantes (alcance solo-detalle, componente nuevo, scroll deshabilitado, sin placeholder sin coordenadas) se cerraron durante `/opsx:explore` y quedaron reflejadas en las Decisiones 1-5 de este documento.
