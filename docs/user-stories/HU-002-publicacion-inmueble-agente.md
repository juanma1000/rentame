# HU-002 — Publicación de inmueble por agente de arrendamiento

## Historia
Como agente de arrendamiento,
quiero publicar y gestionar inmuebles en nombre de un propietario registrado en la plataforma,
para ofrecer el servicio de gestión inmobiliaria de forma digital sin requerir presencia física del propietario en cada paso.

## Criterios de aceptación
- [ ] El agente puede crear una publicación de inmueble con los mismos campos que el propietario (HU-001), pero asociando explícitamente la propiedad a un propietario registrado en la plataforma.
- [ ] El agente debe seleccionar al propietario representado antes de poder publicar un inmueble en su nombre (el propietario debe existir en el sistema).
- [ ] El inmueble publicado por el agente aparece vinculado al propietario representado, visible para ambos en sus respectivos paneles.
- [ ] El agente puede editar los datos de los inmuebles que gestiona.
- [ ] El propietario puede ver, en su panel, los inmuebles que un agente ha publicado en su nombre.
- [ ] El agente no puede publicar inmuebles sin estar asociado a al menos un propietario representado.
- [ ] El estado del inmueble cambia automáticamente a "No disponible" al completarse un arrendamiento, igual que en el flujo del propietario directo.

## Notas técnicas
- **Bloqueo resuelto por HU-007 (Gestión de Agencias), ya implementada**: el mecanismo de asociación entre agente y propietario no es agente-individual↔propietario, sino AGENCIA↔propietario (`backend/agencias/`), con estados `pendiente`/`activa`/`revocada`. El diseño técnico de esta HU debe apoyarse en ese modelo: un agente solo puede publicar/gestionar inmuebles de un propietario si la agencia a la que pertenece (`usuario.agencia_id`) tiene una relación `activa` con ese propietario. La autorización real para `publicar_inmueble`/`editar_inmueble` (que hoy solo aceptan al propietario dueño) todavía no fue extendida para aceptar agentes — es justamente el trabajo pendiente de esta HU.
- `Inmueble.agente_id` ya existe en el dominio y el repositorio (expuesto para HU-007), pero `Inmueble.crear()` no lo acepta como parámetro todavía — esta HU necesita agregarlo ahí, validando la relación agencia↔propietario activa antes de aceptar la publicación.
- Esta HU tiene dependencia funcional con HU-001: comparte el formulario de publicación; la diferencia es la capa de representación/propiedad del inmueble.
- El modelo de permisos debe distinguir el rol Agente del rol Propietario a nivel de acceso y visibilidad.

## Prioridad
Media

## Estimación
05 — Grande (11h)
