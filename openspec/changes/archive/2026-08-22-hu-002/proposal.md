## Why

HU-002 (publicación de inmueble por agente) estaba bloqueada porque no existía ninguna noción de organización agente↔propietario — HU-007 (Gestión de Agencias) resolvió eso. Ahora que la relación `AGENCIA↔propietario` existe y está en verde, falta la mitad que le da sentido de negocio: que un agente pueda de verdad publicar, editar y gestionar inmuebles en nombre de los propietarios vinculados a su agencia. Sin este change, `agencias` es infraestructura sin consumidor real.

## What Changes

- `POST /inmuebles/` acepta un `propietario_id` explícito cuando quien publica es un agente (obligatorio en ese caso; ignorado si publica un propietario, que sigue usando su propio id). El sistema rechaza la publicación si la agencia del agente no tiene una relación `activa` con ese propietario.
- `PUT /inmuebles/{id}` y `PATCH /inmuebles/{id}/disponibilidad` amplían su autorización: además del propietario dueño, cualquier agente cuya agencia tenga relación `activa` con el propietario del inmueble puede editar/cambiar disponibilidad — sin importar si fue ese agente puntual quien lo publicó originalmente.
- Nuevo endpoint `GET /inmuebles/gestionados`: listado de todos los inmuebles de los propietarios vinculados a la agencia del agente autenticado, sin tener que consultar propietario por propietario.
- `Inmueble.crear()` acepta `agente_id` como dato opcional (no lo tenía; el campo ya existía en el dominio/repositorio desde HU-007, pero sin forma de poblarlo al crear).
- La autorización cross-domain (¿la agencia de este agente tiene relación activa con este propietario?) se resuelve en la capa de API de `inmuebles`, consultando los repositorios de `agencias` — los casos de uso de `inmuebles` NO importan nada de `agencias`, preservando la dirección única de dependencia fijada en `design.md` de hu-007.
- Frontend (`inmuebles-app`): el formulario de publicación agrega un selector de propietario cuando la sesión es de un agente; nuevo panel "Inmuebles que gestiono" para agentes.

## Capabilities

### New Capabilities
(ninguna — `agencias` ya existe desde hu-007 y no cambia sus propios requirements en este change)

### Modified Capabilities
- `inmuebles`: MODIFIED "Creación de publicación de inmueble" (acepta agente + propietario_id representado), MODIFIED "Edición de inmueble publicado" (autorización ampliada a nivel agencia), MODIFIED "Despublicación temporal del inmueble" (idem, aplica también a `cambiar_disponibilidad` por agente). ADDED "Listado de inmuebles gestionados por agencia" (nuevo requirement, no modifica uno existente).

## Impact

**Backend**
- `backend/inmuebles/domain/inmueble.py`: `Inmueble.crear()` gana el parámetro opcional `agente_id`. Sin validación de negocio nueva en el dominio — la autorización agencia↔propietario ya se resolvió antes de llegar al caso de uso.
- `backend/inmuebles/application/publicar_inmueble.py`, `editar_inmueble.py`, `cambiar_disponibilidad.py`: comandos ganan un campo opcional `agente_id`/`propietario_id_representado` según corresponda. Los casos de uso siguen sin conocer `agencias`.
- `backend/inmuebles/infrastructure/api/router.py`: cada endpoint que hoy exige `get_current_propietario` pasa a aceptar también `get_current_agente`, resolviendo `propietario_id` de forma distinta según el rol, y consultando los repositorios de `agencias` (inyectados por `Depends`, igual patrón que ya usa `agencias/infrastructure/api/router.py` para consultar `InmuebleRepositoryPostgres`) para el chequeo de autorización antes de invocar el caso de uso.
- Nuevo endpoint `GET /inmuebles/gestionados` en el mismo router.

**Frontend / Microfrontends afectados**
- `inmuebles-app`: `PublicarInmueblePage`/`EditarInmueblePage` agregan un selector de propietario cuando `useAuth().session` tiene rol `agente` (consumiendo `GET /agencias/mia/propietarios`, ya existente). Nueva página/vista "Inmuebles que gestiono".
- `shell`: sin cambios de infraestructura — la ruta existente ya soporta ambos roles vía `AuthGuard`.

**Plan de rollback**
- Backend: los cambios a `publicar_inmueble`/`editar_inmueble`/`cambiar_disponibilidad` son aditivos (parámetros opcionales con default `None`, comportamiento de propietario sin cambios) — revertir el código de este change no requiere migración de datos, ya que `Inmueble.agente_id` sigue siendo nullable y ya existe desde HU-007.
- Frontend: revertir el selector de propietario y el panel nuevo no afecta el flujo de propietario existente (HU-001), que no los usa.
