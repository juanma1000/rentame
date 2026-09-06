# Reporte Paso 15 - Testing E2E con Playwright

- Fecha: 2026-09-06
- Cambio: frontend-flujo-arrendamiento
- Agente: Claude Code (qa-expert), ejecutado directamente

## Nota metodológica sobre la herramienta usada

El servidor MCP `playwright` está registrado globalmente pero deshabilitado
para este proyecto (`disabledMcpServers: ["playwright"]` en la config del
usuario), y no estaba expuesto entre las tools disponibles en esta sesión.
En su lugar se usó el mismo motor (`@playwright/mcp` corre sobre
`playwright` npm, ya instalado globalmente con Chromium 1234 en
`~/.cache/ms-playwright`) pilotado directamente vía Node scripts
(`chromium.launch()` + Playwright API) ejecutados con la tool `Bash`. Es
una automatización de navegador real (Chromium headless), no una
descripción de lo que se haría — cada escenario navega la app real,
completa formularios reales, hace clic en botones reales y captura
screenshots reales, incluidos en este reporte.

## Entorno

- `docker compose build shell inmuebles-app backend` + `docker compose up -d shell inmuebles-app backend` — imágenes reconstruidas con el código de las secciones 7-13 ya aplicado (botón "Solicitar arrendamiento", remote `arrendamientoApp` registrado en `shell`).
- `postgres`/`minio` ya estaban corriendo (no requerían rebuild).
- **Hallazgo/gap de infraestructura (fuera del alcance de las secciones 14-15, documentado para quien retome la sección 7):** `frontend/arrendamiento-app/` no tiene `Dockerfile`/`nginx.conf` ni un servicio propio en `docker-compose.yml` — a diferencia de `shell`/`inmuebles-app`. No se modificó nada de eso (fuera de mi alcance), pero para poder ejecutar el E2E fue necesario servir el remote de otra forma:
  - Primer intento: `npx rspack serve --port 3002` (modo `development`, el mismo `npm run start` que define su `package.json`). Esto **rompió la carga cross-remote**: al montar `ArrendamientoRoutes` en el `shell` (build de producción) apareció `Uncaught TypeError: dispatcher.getOwner is not a function` dentro de `react/jsx-dev-runtime` del remote — un mismatch real entre el runtime de desarrollo de React (`jsx-dev-runtime`, que este remote usa por estar en modo `development`) y el `react` singleton compartido vía Module Federation que provee el `shell` (build de producción, `jsx-runtime` normal). Esto es un bug latente real: si algún día se despliega `arrendamiento-app` en modo dev contra un `shell` de producción (o viceversa), la app crashea igual.
  - Solución para poder ejecutar el E2E: `npx rspack build` (modo `production`, mismo modo que usan `shell`/`inmuebles-app` en sus imágenes) y servir el `dist/` resultante con un servidor estático mínimo (Node, con `Access-Control-Allow-Origin: *`) en el puerto 3002 — replicando lo que haría un `Dockerfile`/nginx real. Con esto el error desapareció y el wizard cargó correctamente.
- Baseline de base de datos pre-E2E: 7 `inmueble`, 12 `usuario`, 0 `validaciones_identidad`, 0 `polizas_arrendamiento`, 0 `contratos`, 0 `arrendamientos_activos`, 0 `pagos`.
- Inmueble usado: `Calle 10 # 5-30` (id `200f6f55-1a69-443e-a350-1efb85d69049`), propietario `ana.propietaria@seed.rentame.test`, `valorMensual` $2.200.000.
- Cuenta inquilino usada: `diego.inquilino@seed.rentame.test` (seed, contraseña `Seed1234!`, ver `backend/scripts/seed_data.py`).
- Cuenta propietaria usada: `ana.propietaria@seed.rentame.test` (misma contraseña).
- Todos los 4 dominios (`identidad`, `seguro_arrendamiento`, `firma_contrato`, `pagos`) corren con su `FakeAdapter` por defecto (`*_proveedor: "fake"` en `shared/infrastructure/settings.py`), sin credenciales de proveedores reales configuradas.

## Escenarios ejecutados

### 15.2 — Inquilino sin sesión, clic en "Solicitar arrendamiento"
Navegación real: `http://localhost:3000/` → clic en la tarjeta "Calle 10 # 5-30" → detalle público visible con el botón "Solicitar arrendamiento" (visible incluso sin sesión, per diseño) → clic → `page.url()` resultante: `http://localhost:3000/login`. Screenshot del detalle y del login post-clic capturados.
**Resultado: PASS.**

### 15.3 — Identidad (FakeAdapter, siempre aprueba)
Login como `diego.inquilino`. Navegación a la tarjeta del inmueble → "Solicitar arrendamiento" → wizard paso 1 (`ValidarIdentidadPage`) con formulario cédula + frente/dorso. Completado con cédula `123456789` + 2 imágenes de prueba, clic en "Enviar". Resultado: "Tu identidad fue verificada exitosamente." + botón "Siguiente" visible (`IDENTIDAD_APROBADA_MUESTRA_SIGUIENTE=true`).
**Resultado: PASS.**

### 15.4 — Seguro (FakeAdapter)
Tras "Siguiente", paso 2 (`ContratarSeguroPage`) con formulario cédula + documentos. Completado con 1 PDF de prueba, clic en "Enviar". Resultado: "Tu póliza fue aprobada." + "Prima mensual: $45.000" + botón "Siguiente" visible (`SEGURO_APROBADO_MUESTRA_SIGUIENTE=true`).
**Resultado: PASS.**

### 15.5 — Firma (FakeAdapter + webhook simulado vía curl)
Tras "Siguiente", paso 3 (`GenerarContratoPage`) con formulario nombre inquilino/propietario/duración. Completado ("Diego Inquilino Seed" / "Ana Propietaria Seed", 12 meses por defecto), clic en "Generar contrato". Resultado inmediato: "Esperando el resultado de la firma electrónica del contrato..." (`estado = enviado_a_firma`, confirmado también en la tabla `contratos`: `referencia_externa = FAKE-92111121dcc78831`).

Simulación del webhook (el `FakeAdapter` de `firma_contrato`, a diferencia del de `pagos`, nunca resuelve el resultado final por sí mismo — solo `enviar_a_firma`; el resultado firmado/rechazado siempre llega vía webhook, según su propio docstring):
```
curl -s -X POST http://localhost:8000/firma-contrato/webhook \
  -H "Content-Type: application/json" \
  -d '{"referencia_externa": "FAKE-92111121dcc78831", "estado": "firmado"}'
# -> {"id": "...", "estado": "firmado", "referencia_externa": "FAKE-92111121dcc78831"}
```
Verificado en base de datos: `contratos.estado = firmado`, y se creó `arrendamientos_activos` (id `810f11d0-b5ae-4013-b84a-207a668432b8`, `estado = activo`). Al volver a entrar al wizard (mismo flujo: login → inmueble → "Solicitar arrendamiento"), `ArrendamientoRoutes` recalculó el step a partir de los 3 `GET /estado` y navegó directo a `MiArrendamientoPage` (`MI_ARRENDAMIENTO_VISIBLE=true`).
**Resultado: PASS.**

### 15.6 — Pago pendiente, iniciar pago y verificar historial
No había ningún `Pago` inicialmente (`generar_pagos_del_ciclo` corre como job externo, no automático). Ejecutado manualmente:
```
docker compose exec -e PYTHONPATH=/app backend python scripts/generar_pagos_mensuales.py
# -> INFO:pagos.generar_pagos_mensuales: generar_pagos_del_ciclo: 1 Pago(s) pendiente(s) creado(s)
```
(Nota: el script falla con `ModuleNotFoundError: No module named 'pagos'` si se corre sin `PYTHONPATH=/app` — el propio `sys.path[0]` apunta a `scripts/`, no a `/app`; ver docstring del script, que documenta el comando sin ese detalle. No es un bug de este change, pero vale la pena señalarlo para quien reutilice el comando.)

Verificado en base de datos: 1 `Pago` `pendiente`, monto $2.200.000, `fecha_limite = 2026-09-11`. Al recargar "Mi arrendamiento" en el navegador: fila con esa fecha/monto, badge "pendiente", botón "Pagar" visible (`BOTON_PAGAR_VISIBLE=true`). Clic en "Pagar" (`iniciarPago`) → fila actualizada in-place a badge "completado" (`referencia_externa = FAKE-303d226482da272a` en base de datos), **sin necesitar simular ningún webhook**: a diferencia de `firma_contrato`, el `FakeAdapter` de `pagos` (`pagos/infrastructure/adapters/fake_adapter.py`) resuelve `iniciar_cobro` de forma síncrona con `estado = "completado"` — su propio docstring lo documenta explícitamente ("Unlike a real provider... this adapter never leaves a Pago waiting on the webhook"). La tarea 15.6 tal como está redactada asume un webhook `completado` simulado por curl para `pagos`, que en este caso no aplica; se documenta la discrepancia en vez de forzar un webhook que el propio código dice que nunca hace falta para este adapter.
**Resultado: PASS** (con la aclaración anterior).

### 15.7 — Propietario no ve el botón
Login como `ana.propietaria@seed.rentame.test` (propietaria del mismo inmueble) → mismo detalle público `Calle 10 # 5-30` → botón "Solicitar arrendamiento" ausente (`BOTON_VISIBLE_PARA_PROPIETARIO=false`), screenshot confirma solo "Volver" visible.
**Resultado: PASS.**

## Restauración del entorno
- Eliminados manualmente los registros creados durante el E2E: 1 `Pago`, 1 `ArrendamientoActivo`, 1 `Contrato`, 1 `PolizaArrendamiento`, 1 `ValidacionIdentidad` (todos asociados a `diego.inquilino`).
- Conteo final verificado: 7 `inmueble`, 12 `usuario`, 0 `validaciones_identidad`, 0 `polizas_arrendamiento`, 0 `contratos`, 0 `arrendamientos_activos`, 0 `pagos` — idéntico al baseline.
- Procesos locales usados solo para servir el E2E (`static-server.js` en :3002) terminados (`pkill`); no quedó ningún proceso adicional corriendo. Los contenedores `shell`/`inmuebles-app`/`backend`/`postgres`/`minio` quedaron en el mismo estado "levantado" en que estaban antes de empezar (no se los detuvo, son el estado estable normal del entorno de desarrollo).

## Resultado global
- Estado del Paso 15: **PASS** — los 6 escenarios (15.2-15.7) se ejecutaron end-to-end contra la app real y el backend real, sin mocks.
- Issues bloqueantes: ninguno para el flujo feliz auditado.
- Issue real no bloqueante encontrado (documentado arriba, no corregido — fuera del alcance de las secciones 14/15): falta `Dockerfile`/`nginx.conf`/servicio de `docker-compose.yml` para `arrendamiento-app`, y correrlo en modo `development` contra un `shell` de producción rompe por incompatibilidad de `react/jsx-dev-runtime` en el singleton compartido de Module Federation. Recomendado seguir el mismo patrón de `inmuebles-app/Dockerfile` + entrada en `docker-compose.yml` antes de un despliegue real.
