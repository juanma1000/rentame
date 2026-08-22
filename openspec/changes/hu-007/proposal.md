## Why

HU-002 (publicación de inmueble por agente) no puede diseñarse ni implementarse porque el sistema no tiene ninguna noción de "agencia": hoy `usuario.rol=agente` es un rol suelto, sin organización a la que pertenezca ni mecanismo para vincularse a un propietario. Sin esa entidad, cualquier vínculo agente-propietario se rompería cada vez que cambia el empleado que atiende a un cliente — Rentame necesita esta capacidad ahora, como fundación de HU-002, no como parte de ella.

## What Changes

- Nueva capacidad `agencias`: entidad `Agencia` (persona jurídica: razón social, NIT), membresía de agentes (un agente pertenece a exactamente una agencia), flujo de ingreso con aprobación de un miembro existente, y salida voluntaria de un agente (bloqueada si es el último miembro con relaciones activas).
- Nueva relación `agencia_propietario` con estados `pendiente` / `activa` / `revocada`, iniciada por el propietario (quien decide contratar una agencia y puede revocarla en cualquier momento), con un puntero "agente responsable" reasignable por cualquier miembro de la agencia (solo trazabilidad, no gatea permisos).
- Un propietario tiene como máximo una agencia con relación `activa` a la vez; contratar una agencia nueva revoca automáticamente la relación activa previa.
- **Efecto en la capacidad `inmuebles` (existente)**: al pasar una relación `agencia_propietario` a `revocada`, los inmuebles del propietario gestionados por esa agencia (los que tengan `agente_id` de un miembro de esa agencia) se despublican automáticamente (pasan a `oculto`), reutilizando la operación `cambiar_disponibilidad` ya existente de HU-001 — no se modifica esa operación, solo se agrega un nuevo caller.

**Fuera de alcance de este change** (queda para el change de HU-002): el formulario de publicación por agente, la selección de propietario representado al publicar, y cualquier endpoint de `inmuebles` que permita a un agente crear/editar inmuebles. Este change deja el modelo organizacional listo para que HU-002 lo consuma, pero no modifica la autorización de `editar_inmueble`/`publicar_inmueble` para aceptar agentes — hoy esos casos de uso siguen aceptando solo al propietario dueño, exactamente como quedaron en HU-001.

## Capabilities

### New Capabilities
- `agencias`: entidad Agencia, membresía de agentes (ingreso con aprobación, salida voluntaria con bloqueo de último-miembro), y la relación agencia↔propietario con su máquina de estados y el puntero de agente responsable.

### Modified Capabilities
- `inmuebles`: se agrega (ADDED, no se modifica ninguna requirement existente) el requirement "Despublicación en cascada por revocación de agencia" — un nuevo trigger que invoca la operación de cambio de disponibilidad ya existente, sin alterar su contrato.

## Impact

**Backend**
- Nuevo dominio `backend/agencias/` (domain, application, infrastructure) siguiendo el patrón hexagonal ya establecido.
- Nuevas tablas: `agencia`, y extensión de la relación agencia-propietario (`agencia_propietario` con estados y `agente_responsable_id`). Nueva migración Alembic. Se agrega `usuario.agencia_id` (FK nullable, solo aplica a `rol=agente`).
- Nuevo caso de uso en `inmuebles` (o un listener/orquestador en `agencias` que invoca `cambiar_disponibilidad` de `inmuebles`) para la despublicación en cascada al revocar.
- Sin cambios en los endpoints existentes de `inmuebles` (`POST /inmuebles/`, `PUT /inmuebles/{id}`, etc.) — siguen aceptando solo al propietario dueño.

**Frontend / Microfrontends afectados**
- Este change es puramente de backend/dominio. No agrega pantallas nuevas al `shell` ni a `inmuebles-app` — la UI de gestión de agencias (crear agencia, aprobar ingresos, ver cartera de propietarios) queda fuera de alcance explícito y se propondrá en un change de frontend posterior (probablemente su propio remote o una sección de `inmuebles-app`, a decidir en `design.md` si aplica, aunque dado que es backend-only se evalúa si hace falta o no).

**Plan de rollback**
- Revertir la migración Alembic (`downgrade`) elimina las tablas nuevas y la columna `usuario.agencia_id` sin afectar `inmuebles` ni `usuarios`, ya que ningún dato existente depende de ellas todavía (greenfield, sin agentes reales usando el sistema hoy).
- El caso de uso de despublicación en cascada es un nuevo caller de `cambiar_disponibilidad`, no una modificación de esa operación — remover el caller no requiere ningún cambio en `inmuebles`.
