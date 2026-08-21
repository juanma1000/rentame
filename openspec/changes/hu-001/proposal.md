## Why

Hoy la publicación de inmuebles depende de agencias que actualizan sistemas de forma manual y con retraso, lo que produce inventario desactualizado (inmuebles que aparecen disponibles cuando ya fueron arrendados). El propietario necesita poder publicar y mantener su propio inmueble directamente en la plataforma — con disponibilidad que se actualice sola cuando se cierra un arrendamiento — para que el inventario sea confiable desde el primer día del MVP, sin depender de intermediación manual.

## What Changes

- Nueva capacidad `inmuebles`: el propietario puede crear una publicación completando dirección, barrio/ciudad, tipo de inmueble, área en m², habitaciones, baños, valor mensual y descripción libre.
- Carga de fotos al publicar: mínimo 1 foto, máximo a definir en `design.md`.
- El inmueble queda con estado `disponible` de forma inmediata tras publicarse exitosamente.
- El propietario puede editar los datos de un inmueble ya publicado.
- El propietario puede despublicar (`oculto`) un inmueble sin eliminarlo, y volver a publicarlo.
- El estado cambia automáticamente a `no_disponible` cuando se completa un arrendamiento sobre ese inmueble (evento disparado desde la capacidad `arrendamiento`, fuera del alcance de este change — acá solo se define el punto de integración).
- El propietario puede ver el listado de sus inmuebles publicados con su estado actual (`disponible` / `no_disponible` / `oculto`).
- Nuevo remote de frontend `inmuebles-app` (microfrontend privado, con sesión) según `docs/architecture/architecture.md`: formulario de publicación/edición y panel "mis inmuebles".
- Nuevo dominio de backend `inmuebles/` (hexagonal) con las entidades `Inmueble` y `FotoInmueble`, casos de uso de publicación/edición/cambio de disponibilidad, y el adaptador de almacenamiento de fotos.

## Capabilities

### New Capabilities
- `inmuebles`: ciclo de vida de la publicación de un inmueble por su propietario — creación, edición, publicación/despublicación manual, listado propio con estado, y el punto de integración para la transición automática a `no_disponible`. Esta capacidad queda abierta a extensión futura por HU-002 (publicación por agente) y HU-003 (búsqueda pública), que se abordarán como specs modificadas en changes posteriores.

### Modified Capabilities
(ninguna — no existen specs previos en `openspec/specs/`; este es el change fundacional del dominio de inmuebles)

## Impact

**Backend**
- Nuevo dominio `backend/inmuebles/` (domain, application, infrastructure) siguiendo el patrón hexagonal de `docs/architecture/architecture.md`.
- Nuevas tablas `inmueble` y `foto_inmueble` (nueva migración Alembic).
- Nuevo adaptador de storage (`StoragePort` → S3/MinIO) para las fotos.

**Frontend / Microfrontends afectados**
- `inmuebles-app`: remote nuevo — formulario de publicación/edición, panel "mis inmuebles".
- `shell`: se agrega la ruta lazy-loaded hacia `inmuebles-app` y el guard de sesión correspondiente.
- Dependencia abierta: este change asume que `shell` (host) y el paquete singleton `@rentame/auth` ya existen o se scaffoldean como parte de la infraestructura mínima de este change — a confirmar en `design.md`, ya que hoy no hay ningún microfrontend implementado todavía.

**Infraestructura**
- Bucket S3/MinIO para fotos de inmuebles (configuración de entorno, no aplica a otros dominios todavía).

**Plan de rollback**
- Backend: revertir la migración Alembic (`downgrade`) elimina las tablas nuevas sin afectar otros dominios, ya que `inmuebles` no tiene todavía dependientes en producción.
- Frontend: remover la entrada de `inmuebles-app` del `shell` (config de Module Federation) y redesplegar el shell sin esa ruta; el remote en sí puede quedar sin desplegar sin romper otros remotes, dado que ninguno depende de `inmuebles-app` como `shared`.
- No hay datos preexistentes que migrar (dominio nuevo), por lo que el rollback no requiere estrategia de backfill.
