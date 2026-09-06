## Why

El PRD (HU-006) exige que el inquilino pague la mensualidad de su arriendo dentro de la plataforma, con trazabilidad y sin efectivo ni transferencias manuales. Hoy, tras un `ArrendamientoActivo` (HU-009, implementado), no existe ningún mecanismo de cobro — es la última pieza del ciclo completo de arrendamiento digital que exige el PRD. Se exploró en sesión previa (`/opsx:explore HU-006`) y se resolvieron los tres puntos abiertos críticos del PRD: proveedor de pasarela (Wompi), modelo de cobro (pull, no débito automático), y mecánica de split (Wompi ejecuta el split nativo vía su API de pagos a terceros, reteniendo la prima de seguro y girando el neto al propietario — Rentame no custodia fondos de terceros).

## What Changes

- Nuevo dominio `pagos`: aggregate `Pago` (pendiente → completado/fallido), vinculado a un `ArrendamientoActivo`, con monto, fecha límite, fecha de pago y referencia externa de la pasarela.
- Job programado (tarea one-off separada, mismo patrón que las migraciones de Alembic en `infra/aws/migrations-task/`) que genera un `Pago` en estado `pendiente` al inicio de cada ciclo mensual de cada `ArrendamientoActivo` — evita el problema de réplicas concurrentes duplicando pagos si se embebiera un scheduler dentro del proceso de la app.
- Puerto `PasarelaPagosPort` con `FakeAdapter` (dev/test, siempre completa el pago) y `WompiAdapter` (prod, contrato exacto pendiente de confirmación comercial — Wompi elegido por tener una "Pagos a Terceros API" documentada públicamente que encaja directo con el split retención-prima/giro-neto).
- Endpoint para que el inquilino inicie el pago de un `Pago` pendiente (pull, no push/débito automático) y webhook que recibe el resultado de Wompi.
- El split de pagos (retener `PolizaArrendamiento.prima_mensual`, girar el resto a `Inmueble.propietario_id`) se ejecuta como parámetros de la transacción de Wompi, no como lógica propia de manejo de fondos.
- Historial de pagos consultable por `ArrendamientoActivo` (pagados, pendientes, fallidos).
- Notificación al propietario cuando el pago se procesa exitosamente queda documentada como requirement, sin implementar — mismo tratamiento que HU-005, porque no existe infraestructura de notificaciones en el proyecto.

## Capabilities

### New Capabilities
- `pagos`: cobro mensual del arriendo vía pasarela externa (Wompi) sobre un `ArrendamientoActivo`, con split nativo de retención de prima y giro al propietario, historial de pagos, y modelo pull (inquilino inicia el pago).

## Impact

- Backend: nuevo paquete `backend/pagos/` (domain/application/infrastructure, mismo patrón hexagonal que `firma_contrato`/`seguro_arrendamiento`/`identidad`/`agencias`/`inmuebles`/`usuarios`); migración Alembic para tabla `pagos`; nueva dependencia HTTP hacia Wompi (solo en `WompiAdapter`); lectura de `ArrendamientoActivo` (dominio `firma_contrato`), `PolizaArrendamiento.prima_mensual` (dominio `seguro_arrendamiento`) e `Inmueble.propietario_id` (dominio `inmuebles`) como precondiciones, sin modificar ninguno.
- Infra: nueva tarea ECS/Fargate one-off para el job mensual de generación de pagos pendientes (mismo patrón que `infra/aws/migrations-task/`), disparada por schedule (EventBridge o equivalente) — el detalle exacto de la infraestructura Terraform es parte de las tareas de este change, no del diseño de dominio.
- Frontend: sin cambio en esta iteración — no hay todavía pantalla de arrendamiento activo ni de pagos; se documenta pero no se construye UI, consistente con HU-004/005/009.
- Fuera de alcance: notificación real al propietario (sin infraestructura de notificaciones), reintentos automáticos de pago fallido más allá de dejar el `Pago` en estado `fallido` consultable, gestión de mora/penalidades por atraso, débito automático (push).
- Rollback: feature aislada y aditiva (nueva tabla, sin tocar dominios existentes salvo lectura); revertir es dropear la migración, el paquete `pagos/` y la tarea ECS del job mensual, sin afectar `firma_contrato`/`seguro_arrendamiento`/`identidad`/`usuarios`/`agencias`/`inmuebles`.
