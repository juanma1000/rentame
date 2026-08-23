## Why

El proyecto tiene 8 HUs implementadas (publicación de inmuebles por propietario/agente, gestión de agencias, registro/login) pero nunca existió una forma de que una persona real *busque* dónde vivir sin antes registrarse. La landing actual del `shell` (`EntradaPage`, HU-008) obliga a elegir un rol de entrada, lo cual no tiene sentido para alguien que solo quiere ver qué inmuebles hay disponibles — decidido tras comparar con un mockup de referencia y explorado en `/opsx:explore HU-003`.

## What Changes

- Nuevo endpoint público `GET /inmuebles/publicos` (sin autenticación): lista todos los inmuebles en estado `disponible`, con los datos mínimos para una tarjeta (foto principal, dirección/barrio, ciudad, valor mensual, habitaciones, baños).
- Nuevo endpoint público `GET /inmuebles/publicos/{id}` (sin autenticación): detalle completo de un inmueble disponible (todas las fotos, descripción, resto de datos).
- **BREAKING (routing del shell)**: la landing (`/`) del `shell` deja de ser `EntradaPage` y pasa a ser el listado público de inmuebles. `EntradaPage` no se elimina — se accede mediante un botón "Publicar mi inmueble" en el header del listado público; un link "Iniciar sesión" en el mismo header lleva a `LoginPage` (ya existente).
- Nuevo componente `BusquedaPublica` (listado + detalle) expuesto por `inmuebles-app` vía Module Federation, reusando el cliente `inmuebles.api.ts` ya existente — mantiene todo el dominio `Inmueble` en un solo microfrontend.
- **Fuera de alcance explícito de esta v1** (no inventar): filtros de búsqueda (ciudad/barrio, precio, habitaciones, tipo) y el botón de "iniciar solicitud de arrendamiento" desde el detalle (bloqueado por HU-005, que no existe todavía). Ambos quedan documentados como diferidos en `docs/user-stories/HU-003-busqueda-inmuebles-disponibles.md`.

## Capabilities

### New Capabilities
Ninguna — esta HU extiende la capacidad `inmuebles` ya existente, no introduce un dominio nuevo.

### Modified Capabilities
- `inmuebles`: ADDED requirements — "Listado público de inmuebles disponibles" y "Detalle público de un inmueble disponible". No se modifica ningún requirement existente (creación, edición, fotos, despublicación, listados privados por propietario/agente).

## Impact

**Backend**
- `backend/inmuebles/application/`: dos nuevos casos de uso de solo lectura (`listar_inmuebles_publicos`, `obtener_inmueble_publico`), sin tocar `inmuebles/domain` (reusan `Inmueble`/`EstadoInmueble` tal como existen desde HU-001).
- `backend/inmuebles/infrastructure/api/router.py`: dos endpoints nuevos, ninguno requiere `Depends` de autenticación.
- `backend/inmuebles/infrastructure/persistence/repository.py`: nuevo método de listado filtrado por `estado == disponible` (puede reusar/extender el repositorio existente).

**Frontend / Microfrontends afectados**
- `inmuebles-app`: nuevo componente `BusquedaPublica` expuesto vía Module Federation (`exposes` en `rspack.config.ts`), reusando `inmuebles.api.ts`.
- `shell`: nueva página que compone el header público (botones "Publicar mi inmueble"/"Iniciar sesión") + el `BusquedaPublica` lazy-cargado; reemplaza `EntradaPage` como ruta `/`. `EntradaPage` se reubica a una ruta propia (ej. `/publicar`) accesible desde ese header.

**Plan de rollback**
- Backend: los dos endpoints nuevos son aditivos puros — revertir el código no requiere migración ni afecta datos existentes.
- Frontend: revertir el cambio de landing es un cambio de código sin dependencias de datos (`App.tsx` vuelve a montar `EntradaPage` en `/`).
