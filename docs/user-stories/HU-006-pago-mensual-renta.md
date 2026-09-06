# HU-006 — Pago mensual de renta

## Historia
Como inquilino,
quiero pagar la mensualidad de mi arriendo dentro de la plataforma mediante medios de pago electrónicos colombianos,
para cumplir con mi obligación de arrendamiento de forma digital, con trazabilidad y sin usar efectivo ni transferencias manuales fuera del sistema.

## Criterios de aceptación
- [ ] El inquilino puede ver en su panel el monto a pagar, la fecha límite de pago y el historial de pagos anteriores. (backend: `GET /arrendamientos/{id}/pagos` devuelve el historial completo con monto/fecha límite; UI de panel es parte de un change de frontend futuro, consistente con HU-004/005/009)
- [x] El sistema habilita el cobro mensual únicamente para arrendamientos activos (contrato firmado exitosamente tras HU-005). (`Pago` solo se genera para un `ArrendamientoActivo`, que a su vez solo existe si `Contrato.estado == firmado`, HU-009)
- [x] El inquilino puede realizar el pago usando al menos un método de pago electrónico compatible con el ecosistema financiero colombiano (ej. tarjeta de crédito/débito, PSE). (vía `WompiAdapter`; método concreto lo determina Wompi en su checkout, no se restringe en el dominio)
- [x] Al completarse el pago exitosamente, el sistema registra la transacción con fecha, monto y referencia de la pasarela de pagos.
- [ ] El propietario recibe una notificación cuando el pago mensual es procesado exitosamente. (documentado como requirement en `specs/pagos/spec.md`; sin implementar — no existe infraestructura de notificaciones en el proyecto, mismo tratamiento que HU-005)
- [x] Si el pago falla, el inquilino recibe una notificación con el motivo del fallo y puede intentarlo nuevamente. (el `Pago` queda en estado `fallido`, consultable; permite reintento manual sobre el mismo registro — el motivo detallado y la notificación en UI quedan para el change de frontend)
- [ ] El inquilino puede descargar o visualizar el comprobante de cada pago realizado. (fuera de alcance de este change — no hay generación de comprobante/PDF; el registro de la transacción sí queda persistido)
- [x] El sistema lleva un registro del historial completo de pagos del contrato (pagados, pendientes, fallidos).

## Notas técnicas
- **Puntos abiertos del PRD resueltos** (decididos en `/opsx:explore HU-006` y `openspec/changes/pago-mensual-renta/design.md`):
  - Proveedor de pasarela: **Wompi** — API descrita como la más moderna del mercado colombiano, con una "Pagos a Terceros API" documentada públicamente que encaja directo con la necesidad de split de esta HU.
  - Modelo de cobro: **pull** — el inquilino inicia el pago manualmente cada ciclo; no hay débito automático (push) en este MVP.
  - Split de pagos / modelo de ingresos: la prima de seguro (HU-005, pagada por el propietario) se retiene y el neto se gira al propietario **dentro de la misma transacción de Wompi** (split nativo vía su API de pagos a terceros) — Rentame no recibe el monto completo para girarlo después por su cuenta, evitando custodiar fondos de terceros.
- El job que genera el `Pago` pendiente de cada ciclo corre como una **tarea ECS/Fargate one-off separada** (no un scheduler embebido en el proceso de la app), mismo patrón ya adoptado para las migraciones de Alembic — el backend corre en réplicas autoescaladas y un scheduler in-process duplicaría pagos por cada réplica.
- Dependencia estricta con HU-009 (arrendamiento activo, implementada) — el pago mensual solo aplica a un `ArrendamientoActivo` ya existente.
- Fuera de alcance: gestión de mora/penalidades por atraso, comprobante descargable, notificación real al propietario, débito automático.

## Prioridad
Alta

## Estimación
08 — Muy Grande (17h)
