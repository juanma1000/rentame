# HU-002 — Publicación de inmueble por agente de arrendamiento

## Historia
Como agente de arrendamiento,
quiero publicar y gestionar inmuebles en nombre de un propietario registrado en la plataforma,
para ofrecer el servicio de gestión inmobiliaria de forma digital sin requerir presencia física del propietario en cada paso.

## Criterios de aceptación
- [x] El agente puede crear una publicación de inmueble con los mismos campos que el propietario (HU-001), pero asociando explícitamente la propiedad a un propietario registrado en la plataforma (mismo endpoint `POST /inmuebles/`, con `propietario_id` obligatorio cuando el llamador es un agente).
- [x] El agente debe seleccionar al propietario representado antes de poder publicar un inmueble en su nombre (el propietario debe existir en el sistema).
- [x] El sistema rechaza la publicación si la agencia del agente no tiene una relación `activa` con el propietario seleccionado.
- [x] El inmueble publicado por el agente aparece vinculado al propietario representado, visible para ambos en sus respectivos paneles.
- [x] El agente puede editar los datos de cualquier inmueble de un propietario vinculado a su agencia (relación `activa`), sin importar si fue él u otro agente de la misma agencia quien lo publicó originalmente.
- [x] El agente puede despublicar/republicar (cambiar disponibilidad) los inmuebles de los propietarios vinculados a su agencia, con la misma regla de autorización a nivel agencia que la edición.
- [x] El propietario puede ver, en su panel, los inmuebles que un agente ha publicado en su nombre.
- [x] El agente puede ver un listado propio de todos los inmuebles que gestiona (de todos los propietarios vinculados a su agencia), sin tener que entrar propietario por propietario.
- [x] El agente no puede publicar ni gestionar inmuebles sin estar asociado a al menos un propietario representado con relación `activa`.
- [x] Si la relación agencia↔propietario deja de estar `activa` (revocada), ningún agente de esa agencia puede seguir editando o cambiando la disponibilidad de los inmuebles de ese propietario, además de la despublicación automática ya cubierta por HU-007.
- [ ] El estado del inmueble cambia automáticamente a "No disponible" al completarse un arrendamiento, igual que en el flujo del propietario directo. — **Fuera de alcance de este change**: depende de HU-005 (arrendamiento), que todavía no existe. Mismo estado pendiente que quedó en HU-001.

## Notas técnicas
- **Bloqueo resuelto por HU-007 (Gestión de Agencias), ya implementada**: el mecanismo de asociación entre agente y propietario no es agente-individual↔propietario, sino AGENCIA↔propietario (`backend/agencias/`), con estados `pendiente`/`activa`/`revocada`. Un agente solo puede publicar/gestionar inmuebles de un propietario si la agencia a la que pertenece (`usuario.agencia_id`) tiene una relación `activa` con ese propietario.
- **Dirección de dependencia entre dominios (decisión de diseño, no reabrir)**: la autorización cross-domain (¿la agencia del agente tiene relación activa con este propietario?) se resuelve en la capa de API de `inmuebles` (el router consulta `agencias` antes de invocar el caso de uso), no dentro de los casos de uso de `inmuebles`. Esto evita que `inmuebles/application` importe nada de `agencias`, preservando la regla de una sola dirección fijada en `design.md` de hu-007 (`agencias` conoce a `inmuebles`, nunca al revés).
- **La autorización es a nivel agencia, no a nivel agente individual**: el check es "¿la agencia del agente que llama tiene relación activa con `inmueble.propietario_id`?", nunca "¿`token.sub == inmueble.agente_id`?". Esto es intencional — mismo criterio que hu-007 (sin jerarquía interna, cualquier agente de la agencia gestiona cualquier propietario vinculado). Aplica igual a `editar_inmueble` y a `cambiar_disponibilidad`.
- `Inmueble.agente_id` ya existe en el dominio y el repositorio (expuesto para HU-007), pero `Inmueble.crear()` no lo acepta como parámetro todavía — esta HU necesita agregarlo ahí como dato opcional. El dominio `Inmueble` NO valida la relación agencia↔propietario (esa autorización ya se resolvió antes, en la capa de API) — solo almacena el dato.
- Al editar un inmueble, `agente_id` NO se actualiza al agente que edita — sigue siempre apuntando a quién lo publicó originalmente (dato de auditoría, no de autorización).
- Nuevo requerimiento de listado: el agente necesita una vista propia de "inmuebles que gestiono" (todos los propietarios vinculados a su agencia), no solo poder navegar la cartera de `GET /agencias/mia/propietarios` uno por uno.
- Esta HU tiene dependencia funcional con HU-001: comparte el formulario de publicación; la diferencia es la capa de representación/propiedad del inmueble.
- El modelo de permisos debe distinguir el rol Agente del rol Propietario a nivel de acceso y visibilidad.

## Prioridad
Media

## Estimación
05 — Grande (11h)

Nota: esta estimación es anterior a la exploración que agregó el listado propio del agente y la resolución explícita de la autorización cross-domain con `agencias`. Vale la pena que quien ejecute `/opsx:propose` reevalúe si sigue siendo un 05 o si escala, dado el trabajo adicional descubierto.
