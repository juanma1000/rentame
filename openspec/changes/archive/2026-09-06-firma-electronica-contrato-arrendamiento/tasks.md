## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/firma-electronica-contrato-arrendamiento` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: dominio `firma-contrato` — aggregates y puertos

- [x] 1.1 qa-expert (Red): tests unitarios de `Contrato` — creación en `borrador`, transiciones (`borrador`→`enviado_a_firma`→`firmado`/`rechazado`/`expirado`), invariante de que un contrato `firmado` no puede volver a `enviado_a_firma`
- [x] 1.2 backend-expert (Green): `backend/firma_contrato/domain/contrato.py` (aggregate `Contrato`)
- [x] 1.3 qa-expert (Red): tests unitarios de `ArrendamientoActivo` — creación solo posible a partir de un `Contrato` en estado `firmado`
- [x] 1.4 backend-expert (Green): `backend/firma_contrato/domain/arrendamiento_activo.py`
- [x] 1.5 backend-expert: `backend/firma_contrato/domain/ports.py` — `ProveedorFirmaElectronicaPort` (`.enviar_a_firma(documento) -> ResultadoEnvioFirma`), `ContratoRepositoryPort`, `ArrendamientoActivoRepositoryPort`, `PolizaArrendamientoPort` (lectura de solo lectura sobre `PolizaArrendamiento.estado`, mismo patrón que `UsuarioIdentidadPort` de `seguro_arrendamiento`)
- [x] 1.6 backend-expert: `backend/firma_contrato/domain/exceptions.py` (revisar primero si `docs/architecture/architecture.md` ya documenta nombres específicos para este dominio antes de inventar los propios; si no, usar nombres consistentes con el resto del proyecto, sin sufijo `Error`)

## 2. Backend: `FakeAdapter` para dev/test

- [x] 2.1 qa-expert (Red): test de `FakeAdapter.enviar_a_firma(...)` — siempre retorna resultado `firmado` con `referencia_externa` determinística
- [x] 2.2 backend-expert (Green): `backend/firma_contrato/infrastructure/adapters/fake_adapter.py`

## 3. Backend: caso de uso `generar_contrato`

- [x] 3.1 qa-expert (Red): tests con `FakeAdapter` inyectado — inquilino sin `PolizaArrendamiento` aprobada se rechaza SIN generar documento ni llamar al proveedor; inquilino con póliza aprobada genera contrato en `borrador`, lo envía a firma y queda en `enviado_a_firma`
- [x] 3.2 backend-expert (Green): `backend/firma_contrato/application/generar_contrato.py` (incluye la generación del documento vía template propio, ver tarea 3.3)
- [x] 3.3 backend-expert: template de generación del documento del contrato (texto legal con partes, canon, duración mínima 6 meses según el PRD) — función/módulo propio, sin depender del proveedor de firma para el contenido

## 4. Backend: caso de uso `procesar_resultado_firma` (webhook)

- [x] 4.1 qa-expert (Red): tests — resultado `firmado` marca el contrato como `firmado` y crea `ArrendamientoActivo`; resultado `rechazado`/`expirado` marca el contrato con ese estado sin crear `ArrendamientoActivo` ni tocar la póliza asociada
- [x] 4.2 backend-expert (Green): `backend/firma_contrato/application/procesar_resultado_firma.py`

## 5. Backend: persistencia

- [x] 5.1 qa-expert (Red): tests de integración de `ContratoRepositoryPostgres`/`ArrendamientoActivoRepositoryPostgres` contra Postgres real — crear, listar por `usuario_id`
- [x] 5.2 backend-expert (Green): `backend/firma_contrato/infrastructure/persistence/models.py` + `repository.py` (tablas `contratos` y `arrendamientos_activos`)
- [x] 5.3 backend-expert: migración Alembic — tabla `contratos` (usuario_id FK, poliza_id FK, estado, documento_referencia, referencia_externa) y tabla `arrendamientos_activos` (usuario_id FK, contrato_id FK, inmueble_id, fecha_inicio, estado)

## 6. Backend: endpoints

- [x] 6.1 qa-expert (Red): tests de integración `POST /firma-contrato/generar` — sin póliza aprobada retorna error explícito; con póliza aprobada retorna 200 con estado `enviado_a_firma`
- [x] 6.2 backend-expert (Green): `backend/firma_contrato/infrastructure/api/router.py` (endpoint `/generar`) + `schemas.py`
- [x] 6.3 qa-expert (Red): tests de integración `POST /firma-contrato/webhook` — payload simulado de Viafirma para cada resultado (firmado/rechazado/expirado), verifica el efecto correcto en `Contrato`/`ArrendamientoActivo`
- [x] 6.4 backend-expert (Green): endpoint `/webhook` en el mismo router

## 7. Backend: `ViafirmaAdapter` (adapter real)

- [x] 7.1 qa-expert (Red): tests con HTTP client mockeado — mapeo correcto del envío a firma; manejo explícito de timeout/error (no 500, estado claro de "envío a firma no disponible")
- [x] 7.2 backend-expert (Green): `backend/firma_contrato/infrastructure/adapters/viafirma_adapter.py` (contrato exacto de payload/respuesta es open question de design.md — implementar la forma más razonable, aislada detrás del puerto)
- [x] 7.3 backend-expert: configuración por ambiente para seleccionar `FakeAdapter` (default) vs `ViafirmaAdapter` (prod), mismo mecanismo que `identidad.infrastructure.proveedor`/`seguro_arrendamiento.infrastructure.proveedor`

## 8. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 8.1 Revisar suite completa de `backend/tests/` en busca de fixtures/tests afectados por el nuevo dominio (lectura de `PolizaArrendamiento.estado`, sin modificarlo) — confirmar que no hace falta ningún cambio
- [x] 8.2 Confirmar que ningún test existente de `seguro_arrendamiento`/`identidad`/`usuarios`/`agencias`/`inmuebles` se rompe por el cambio (puramente aditivo, nuevas tablas)

## 9. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 9.1 Capturar el baseline de base de datos pre-test (conteo de filas en `usuarios`, `validaciones_identidad`, `polizas_arrendamiento`; tablas `contratos`/`arrendamientos_activos` no deben existir aún si es la primera corrida tras la migración)
- [x] 9.2 Correr los unit tests focalizados de `firma-contrato` vía `docker compose exec backend pytest tests/firma_contrato`
- [x] 9.3 Correr la suite completa vía `docker compose exec backend pytest`
- [x] 9.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [x] 9.5 Crear el reporte `openspec/changes/firma-electronica-contrato-arrendamiento/specs/reports/YYYY-MM-DD-step-9-unit-test-and-db-verification.md`
- [x] 9.6 Marcar este paso como completo solo después de que los tests pasen y el reporte exista

## 10. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 10.1 `docker compose up` con rebuild del backend tras la migración
- [x] 10.2 curl: `POST /firma-contrato/generar` con una cuenta inquilino con póliza aprobada — verificar 200 y estado `enviado_a_firma`
- [x] 10.3 curl: mismo endpoint con cuenta inquilino SIN póliza aprobada — verificar rechazo explícito sin generar documento
- [x] 10.4 curl: `POST /firma-contrato/webhook` simulando resultado `firmado` — verificar que se creó `ArrendamientoActivo`
- [x] 10.5 curl: `POST /firma-contrato/webhook` simulando resultado `rechazado` — verificar que NO se creó `ArrendamientoActivo` y que la póliza sigue `aprobada`
- [x] 10.6 Documentar los resultados en `openspec/changes/firma-electronica-contrato-arrendamiento/specs/reports/YYYY-MM-DD-step-10-manual-curl-testing.md`

## 11. Documentación (OBLIGATORIO)

- [x] 11.1 Actualizar `docs/architecture/architecture.md` con el nuevo dominio `backend/firma_contrato/`, sus puertos/adapters, y las tablas `contratos`/`arrendamientos_activos`
- [x] 11.2 Crear `docs/user-stories/HU-009-firma-electronica-contrato-arrendamiento.md` con la historia, criterios de aceptación marcados, y notas técnicas (proveedor Viafirma, decisión de separarla de HU-005, dependencia con HU-006)
