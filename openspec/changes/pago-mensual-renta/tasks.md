## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/pago-mensual-renta` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: dominio `pagos` — aggregate y puertos

- [x] 1.1 qa-expert (Red): tests unitarios de `Pago` — creación en `pendiente`, transición a `completado`/`fallido`, invariante de que un pago `completado` no puede volver a `pendiente`
- [x] 1.2 backend-expert (Green): `backend/pagos/domain/pago.py` (aggregate `Pago`)
- [x] 1.3 backend-expert: `backend/pagos/domain/ports.py` — `PasarelaPagosPort` (`.iniciar_cobro(monto, split) -> ResultadoCobro`), `PagoRepositoryPort`, `ArrendamientoActivoPort` (lectura de solo lectura sobre `ArrendamientoActivo`, mismo patrón que `PolizaArrendamientoPort` de `firma_contrato`), `PolizaArrendamientoPort` (lectura de `prima_mensual`), `InmueblePort` (lectura de `propietario_id`)
- [x] 1.4 backend-expert: `backend/pagos/domain/exceptions.py` (revisar primero si `docs/architecture/architecture.md` ya documenta nombres específicos para este dominio antes de inventar los propios; si no, usar nombres consistentes con el resto del proyecto, sin sufijo `Error`)

## 2. Backend: `FakeAdapter` para dev/test

- [x] 2.1 qa-expert (Red): test de `FakeAdapter.iniciar_cobro(...)` — siempre retorna resultado `completado` con `referencia_externa` determinística
- [x] 2.2 backend-expert (Green): `backend/pagos/infrastructure/adapters/fake_adapter.py`

## 3. Backend: caso de uso `generar_pagos_del_ciclo` (job mensual)

- [x] 3.1 qa-expert (Red): tests — genera exactamente un `Pago` pendiente por cada `ArrendamientoActivo` activo; no genera un segundo `Pago` pendiente si ya existe uno sin resolver para el ciclo actual (idempotencia)
- [x] 3.2 backend-expert (Green): `backend/pagos/application/generar_pagos_del_ciclo.py`

## 4. Backend: caso de uso `iniciar_pago`

- [x] 4.1 qa-expert (Red): tests con `FakeAdapter` inyectado — arma el split (monto total, prima a retener vía `PolizaArrendamiento.prima_mensual`, neto al propietario vía `Inmueble.propietario_id`) a partir de `ArrendamientoActivo`; un `Pago` ya `completado` no puede reiniciarse; pago inexistente se rechaza
- [x] 4.2 backend-expert (Green): `backend/pagos/application/iniciar_pago.py`

## 5. Backend: caso de uso `procesar_resultado_pago` (webhook)

- [x] 5.1 qa-expert (Red): tests — resultado `completado` marca el `Pago` con fecha de pago; resultado `fallido` marca el `Pago` sin más efectos
- [x] 5.2 backend-expert (Green): `backend/pagos/application/procesar_resultado_pago.py`

## 6. Backend: persistencia

- [x] 6.1 qa-expert (Red): tests de integración de `PagoRepositoryPostgres` contra Postgres real — crear, listar por `arrendamiento_activo_id` (historial completo, cualquier estado)
- [x] 6.2 backend-expert (Green): `backend/pagos/infrastructure/persistence/models.py` + `repository.py` (tabla `pagos`)
- [x] 6.3 backend-expert: migración Alembic — tabla `pagos` (arrendamiento_activo_id FK, estado, monto, fecha_limite, fecha_pago, referencia_externa)

## 7. Backend: endpoints

- [x] 7.1 qa-expert (Red): tests de integración `POST /pagos/{id}/iniciar` — pago inexistente retorna 404; pago ya completado retorna error explícito; pago pendiente válido retorna 200
- [x] 7.2 backend-expert (Green): `backend/pagos/infrastructure/api/router.py` (endpoint `/iniciar`) + `schemas.py`
- [x] 7.3 qa-expert (Red): tests de integración `POST /pagos/webhook` — payload simulado de Wompi para resultado `completado` y `fallido`, verifica el efecto correcto en `Pago`
- [x] 7.4 backend-expert (Green): endpoint `/webhook` en el mismo router
- [x] 7.5 qa-expert (Red): tests de integración `GET /arrendamientos/{id}/pagos` — historial completo sin filtrar por estado
- [x] 7.6 backend-expert (Green): endpoint de historial en el mismo router

## 8. Backend: `WompiAdapter` (adapter real)

- [x] 8.1 qa-expert (Red): tests con HTTP client mockeado — mapeo correcto del cobro con split; manejo explícito de timeout/error (no 500, estado claro de "cobro no disponible")
- [x] 8.2 backend-expert (Green): `backend/pagos/infrastructure/adapters/wompi_adapter.py` (contrato exacto de payload/respuesta del split es open question de design.md — implementar la forma más razonable, aislada detrás del puerto)
- [x] 8.3 backend-expert: configuración por ambiente para seleccionar `FakeAdapter` (default) vs `WompiAdapter` (prod), mismo mecanismo que los tres dominios anteriores

## 9. Infra: job mensual como tarea ECS/Fargate one-off

- [x] 9.1 backend-expert: entrypoint/script que invoca `generar_pagos_del_ciclo` (mismo patrón que el entrypoint de migraciones en `backend/docker-entrypoint.sh`/`infra/aws/migrations-task/`)
- [x] 9.2 qa-expert (Red): test de integración que confirma que el script corre contra la base real y es idempotente si se ejecuta dos veces en el mismo ciclo
- [x] 9.3 backend-expert: `infra/aws/pagos-mensuales-task/main.tf` + `variables.tf` (mismo patrón que `infra/aws/migrations-task/`), con su schedule (EventBridge o equivalente) disparando la tarea una vez al mes

## 10. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 10.1 Revisar suite completa de `backend/tests/` en busca de fixtures/tests afectados por el nuevo dominio (lectura de `ArrendamientoActivo`/`PolizaArrendamiento`/`Inmueble`, sin modificarlos) — confirmar que no hace falta ningún cambio
- [x] 10.2 Confirmar que ningún test existente de `firma_contrato`/`seguro_arrendamiento`/`identidad`/`usuarios`/`agencias`/`inmuebles` se rompe por el cambio (puramente aditivo, nueva tabla)

## 11. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 11.1 Capturar el baseline de base de datos pre-test (conteo de filas en `usuarios`, `validaciones_identidad`, `polizas_arrendamiento`, `contratos`, `arrendamientos_activos`; tabla `pagos` no debe existir aún si es la primera corrida tras la migración)
- [x] 11.2 Correr los unit tests focalizados de `pagos` vía `docker compose exec backend pytest tests/pagos`
- [x] 11.3 Correr la suite completa vía `docker compose exec backend pytest`
- [x] 11.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [x] 11.5 Crear el reporte `openspec/changes/pago-mensual-renta/specs/reports/YYYY-MM-DD-step-11-unit-test-and-db-verification.md`
- [x] 11.6 Marcar este paso como completo solo después de que los tests pasen y el reporte exista

## 12. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 12.1 `docker compose up` con rebuild del backend tras la migración
- [x] 12.2 curl: correr manualmente `generar_pagos_del_ciclo` sobre un `ArrendamientoActivo` de prueba (construir la cadena completa: identidad → seguro → firma-contrato → arrendamiento activo) — verificar que se crea un `Pago` pendiente
- [x] 12.3 curl: correrlo una segunda vez — verificar que NO se crea un segundo `Pago` pendiente (idempotencia)
- [x] 12.4 curl: `POST /pagos/{id}/iniciar` sobre el pago pendiente — verificar 200
- [x] 12.5 curl: `POST /pagos/webhook` simulando resultado `completado` — verificar que el `Pago` queda `completado` con fecha de pago
- [x] 12.6 curl: `GET /arrendamientos/{id}/pagos` — verificar que el historial muestra el pago completado
- [x] 12.7 Documentar los resultados en `openspec/changes/pago-mensual-renta/specs/reports/YYYY-MM-DD-step-12-manual-curl-testing.md`

## 13. Documentación (OBLIGATORIO)

- [x] 13.1 Actualizar `docs/architecture/architecture.md` con el nuevo dominio `backend/pagos/`, sus puertos/adapters, la tabla `pagos`, y la tarea ECS del job mensual
- [x] 13.2 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-006-pago-mensual-renta.md`, anotar que el proveedor elegido es Wompi (pull, split nativo) — resolviendo los puntos abiertos del PRD
