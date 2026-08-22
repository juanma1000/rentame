# Reporte Paso 14 - Testing E2E con Playwright MCP

- Fecha: 2026-08-21
- Cambio: hu-002
- Agente: Claude (sesión principal, Playwright MCP)

## Entorno

- Backend: `rentame-backend` (Docker, bind mount + `--reload`), rama `feature/hu-002-backend` mergeada temporalmente en `feature/hu-002-inmuebles-app` para poder correr backend + frontend juntos.
- Frontend: `rentame-shell` (:3000), `rentame-inmuebles-app` (:3001), imágenes reconstruidas desde cero (`docker compose build` sin cache previa a este paso).
- Datos de prueba: María (propietaria), Agente A (crea la agencia), Agente B (se une a la agencia de A, aprobado por A) — todo vía la API real, no fixtures directas a DB salvo la creación inicial de los 3 usuarios.

## Bloqueo encontrado y resuelto

Playwright MCP se desconectó de la sesión a mitad del change (servidor MCP, no relacionado a Docker/código). Se pausó, se le pidió al usuario reconectarlo, y se retomó una vez reconectado — confirmado con una llamada de prueba antes de arrancar.

## Escenarios ejecutados

1. **Login como Agente A** (`/`, pegar JWT) → sesión inicializada.
2. **Navegación a `/mis-inmuebles` como agente**: monta `InmueblesGestionadosPage` (no `MisInmueblesPage`) — confirma el wiring por rol en `PropertyRoutes`. Lista vacía, botón "Publicar nuevo inmueble" visible.
3. **Publicar como agente**: formulario completo + selector de propietario (poblado con `maria-e2e@test.com` desde `GET /agencias/mia/propietarios`, incluyendo el `propietario_email` real) + 1 foto → publica exitosamente → vuelve a "Inmuebles que gestiono", aparece como Disponible.
4. **Edición cruzada (Agente B, mismo agencia, no publicó el inmueble)**: login como Agente B → `/mis-inmuebles` muestra el mismo inmueble en su cartera (confirma autorización a nivel agencia, no a nivel publicador individual) → edita el valor mensual (1.800.000 → 1.950.000) → guarda.
5. **Verificación de inmutabilidad de `agente_id`**: `curl GET /inmuebles/gestionados` (como Agente A) tras la edición de B confirma `valor_mensual=1950000.0` (persistido) y `agente_id` sigue siendo el de Agente A (nunca cambia por edición de otro agente de la misma agencia).
6. **Propietario ve el inmueble en su propio panel**: login como María → `/mis-inmuebles` monta `MisInmueblesPage` (rol propietario) → el inmueble publicado por el agente aparece en su listado, con control total (botones Despublicar/Editar) — confirma el criterio de aceptación "el propietario puede ver, en su panel, los inmuebles que un agente ha publicado en su nombre".

## Restauración de entorno

- DB de desarrollo: eliminados en orden seguro (solicitudes → relaciones → fotos → inmuebles → agencias → usuarios de prueba). Verificado post-limpieza: `usuario=1` (el demo-owner preexistente antes de esta sesión, intacto), `inmueble=0`, `agencia=0`, `relacion_agencia_propietario=0`, `solicitud_ingreso_agencia=0`.
- MinIO: 0 objetos remanentes tras la limpieza.

## Resultado

- Estado del Paso 14: **PASS**.
- Issues bloqueantes: ninguno pendiente (el bloqueo de Playwright MCP fue de infraestructura de sesión, no de código, y se resolvió reconectando).
- Ningún bug de código encontrado durante este paso — el diseño de autorización a nivel agencia (Decisión 3 de `design.md`) y la inmutabilidad de `agente_id` (Decisión 5) funcionan exactamente como estaban especificados.
