# Reporte Paso 12 - Testing E2E con Playwright MCP

- Fecha: 2026-08-22
- Cambio: hu-008
- Agente: Claude Code (Playwright MCP real, navegador headless controlado por herramientas MCP)

Entorno: `docker compose up` con `shell` (rebuild con el código nuevo), `backend`, `postgres`, `inmuebles-app`. Baseline pre-test: `usuario`=8, `agencia`=1, `inmueble`=4 (dev DB).

## Bug real encontrado y corregido durante el E2E

Al navegar directamente a `http://localhost:3000/registro/agente` (carga completa de página, no navegación client-side), la consola mostraba `Unexpected token '<'` y la app quedaba en blanco. Causa: `frontend/shell/rspack.config.ts` usaba `output.publicPath: 'auto'`, que Rspack resuelve contra la URL actual del documento. Como nginx sirve `index.html` para cualquier ruta desconocida (fallback de SPA), al servir `/registro/agente` el navegador resolvía el `<script src="main.js">` relativo como `/registro/main.js` → nginx devolvía `index.html` (contenido HTML) con status 200 pero interpretado como JS → error de parseo y pantalla en blanco.

**Este es, con alta probabilidad, el mismo bug de "pantalla en blanco" reportado por el usuario anteriormente en la sesión** (nunca confirmado como resuelto). Corregido cambiando `publicPath` a `'/'` (absoluto) en `frontend/shell/rspack.config.ts`, rebuild de la imagen `shell`, reverificado: la misma navegación directa ya no produce error de consola ni pantalla en blanco.

## Escenarios ejecutados

### 12.2 — Registro completo como propietario
1. `http://localhost:3000/` → 3 opciones visibles simétricamente.
2. Clic en "Quiero publicar mi inmueble" → `/registro/propietario`.
3. Formulario completado (email/password/nombre) → "Registrarme".
4. Resultado: redirect automático a `/mis-inmuebles` (página real de `inmuebles-app` cargada vía Module Federation), **sin volver a loguearse** — sesión persistida por `useAuth().login(accessToken)`.

### 12.3 — Registro de agente creando agencia nueva
1. `/registro/agente` → formulario → "Registrarme".
2. Sin redirect inmediato: muestra paso "Configura tu agencia" con opciones "Crear agencia nueva" / "Unirme a una agencia existente".
3. "Crear agencia nueva" → formulario razón social + NIT → "Crear agencia".
4. Resultado: redirect a `/mis-inmuebles`. Verificado en Postgres: `usuario.agencia_id` del agente apunta a la agencia recién creada (`JOIN` exitoso).

### 12.4 — Registro de agente uniéndose a agencia existente
1. Segundo agente se registra → paso de agencia → "Unirme a una agencia existente".
2. Busca "E2E Agencia Uno" → `GET /agencias/buscar` (sin auth) devuelve la agencia creada en el escenario anterior.
3. "Solicitar unirme" → UI muestra "Solicitud pendiente" (no error).
4. Verificado en Postgres: fila en `solicitud_ingreso_agencia` con `estado='pendiente'` para ese agente.

### 12.5 — Login con credenciales inválidas
1. `/login` con email válido + password incorrecto.
2. UI muestra `role="alert"`: "Email o contraseña incorrectos" — sin crash, sin redirect. (Consola registra el 401 del fetch, esperado, no es un error de aplicación.)

### 12.6 — Búsqueda pública de inmuebles sin sesión
No aplica: HU-003 (búsqueda pública de inmuebles) todavía no está implementada en el backend (`GET /openapi.json` confirma que no existe ese endpoint). La tarea es condicional ("si ya implementada") — se deja pendiente para cuando HU-003 exista.

## Restauración del entorno
```sql
DELETE FROM inmueble WHERE propietario_id IN (SELECT id FROM usuario WHERE email LIKE 'e2e.%@rentame.test');
DELETE FROM solicitud_ingreso_agencia WHERE agente_id IN (SELECT id FROM usuario WHERE email LIKE 'e2e.%@rentame.test');
DELETE FROM relacion_agencia_propietario WHERE propietario_id IN (SELECT id FROM usuario WHERE email LIKE 'e2e.%@rentame.test');
UPDATE usuario SET agencia_id = NULL WHERE email LIKE 'e2e.%@rentame.test';
DELETE FROM usuario WHERE email LIKE 'e2e.%@rentame.test';
DELETE FROM agencia WHERE nit = 'E2E-111222333';
```
Conteos post-limpieza: `usuario`=8, `agencia`=1, `inmueble`=4 — idénticos al baseline. Sesión del navegador cerrada.

## Resultado
- Estado del Paso 12: PASS (12.6 no aplicable, HU-003 pendiente)
- Issue real encontrado y corregido: `publicPath: 'auto'` → `'/'` en `frontend/shell/rspack.config.ts` (pantalla en blanco en navegación directa a rutas anidadas)
- Issues bloqueantes: ninguno
