## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/seguro-arrendamiento-inquilino` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: dominio `seguro-arrendamiento` — aggregate y puerto

- [x] 1.1 qa-expert (Red): tests unitarios de `PolizaArrendamiento` — creación, transiciones de estado (`pendiente`→`aprobada`/`rechazada`, `aprobada`→`activa`→`vencida`), invariante de que una póliza `rechazada` no puede activarse
- [x] 1.2 backend-expert (Green): `backend/seguro-arrendamiento/domain/poliza_arrendamiento.py` (aggregate `PolizaArrendamiento`)
- [x] 1.3 backend-expert: `backend/seguro-arrendamiento/domain/ports.py` — `ProveedorSeguroArrendamientoPort` (interfaz `contratar(cedula, documentos) -> ResultadoPoliza`), `PolizaArrendamientoRepositoryPort`, `UsuarioIdentidadPort` (lectura de `identidad_verificada`, mismo patrón que `identidad.domain.ports.UsuarioIdentidadRepositoryPort`)
- [x] 1.4 backend-expert: `backend/seguro-arrendamiento/domain/exceptions.py` (ej. `IdentidadNoVerificada`, `ContratacionNoDisponible`)

## 2. Backend: `FakeAdapter` para dev/test

- [x] 2.1 qa-expert (Red): test de `FakeAdapter.contratar(...)` — siempre retorna `aprobada` con `prima_mensual` y `referencia_externa` determinísticas
- [x] 2.2 backend-expert (Green): `backend/seguro-arrendamiento/infrastructure/adapters/fake_adapter.py`

## 3. Backend: caso de uso `contratar_seguro_arrendamiento`

- [x] 3.1 qa-expert (Red): tests con `FakeAdapter` inyectado — inquilino sin `identidad_verificada` se rechaza SIN llamar al proveedor de seguro; inquilino verificado y aprobado crea `PolizaArrendamiento` en estado `aprobada`
- [x] 3.2 qa-expert (Red): test con stub propio del puerto simulando rechazo — persiste el intento en estado `rechazada`, no habilita avance
- [x] 3.3 backend-expert (Green): `backend/seguro-arrendamiento/application/contratar_seguro_arrendamiento.py`

## 4. Backend: persistencia

- [x] 4.1 qa-expert (Red): test de integración de `PolizaArrendamientoRepositoryPostgres` contra Postgres real — crear, listar por `usuario_id`
- [x] 4.2 backend-expert (Green): `backend/seguro-arrendamiento/infrastructure/persistence/models.py` + `repository.py` (tabla `polizas_arrendamiento`)
- [x] 4.3 backend-expert: migración Alembic — tabla `polizas_arrendamiento` (usuario_id FK, estado, prima_mensual, vigencia_desde, vigencia_hasta, referencia_externa)

## 5. Backend: endpoint proxy

- [x] 5.1 qa-expert (Red): tests de integración `POST /seguro-arrendamiento/contratar` — payload válido con documentos retorna 200 con estado esperado; payload sin documentos retorna 422; inquilino sin identidad verificada retorna error explícito sin llamar al proveedor
- [x] 5.2 qa-expert (Red): test explícito que verifica que los bytes de los documentos NO quedan persistidos en ninguna tabla/archivo tras la llamada
- [x] 5.3 backend-expert (Green): `backend/seguro-arrendamiento/infrastructure/api/router.py` + `schemas.py` — recibe multipart (documentos de soporte), verifica identidad verificada, reenvía al puerto, descarta bytes tras la respuesta

## 6. Backend: `SuraAdapter` (adapter real)

- [x] 6.1 qa-expert (Red): tests con HTTP client mockeado — mapeo correcto de respuesta a `ResultadoPoliza`; manejo explícito de timeout/error de la API externa (no 500, estado claro de "contratación no disponible")
- [x] 6.2 backend-expert (Green): `backend/seguro-arrendamiento/infrastructure/adapters/sura_adapter.py` (contrato exacto de payload/respuesta es open question de design.md — implementar la forma más razonable, aislada detrás del puerto)
- [x] 6.3 backend-expert: configuración por ambiente para seleccionar `FakeAdapter` (default) vs `SuraAdapter` (prod, requiere credenciales configuradas), mismo mecanismo que `identidad.infrastructure.proveedor`

## 7. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 7.1 Revisar suite completa de `backend/tests/` en busca de fixtures/tests afectados por el nuevo dominio (lectura de `usuario.identidad_verificada`, sin modificarlo) — confirmar que no hace falta ningún cambio
- [x] 7.2 Confirmar que ningún test existente de `identidad`/`usuarios`/`agencias`/`inmuebles` se rompe por el cambio (puramente aditivo, nueva tabla)

## 8. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 8.1 Capturar el baseline de base de datos pre-test (conteo de filas en `usuarios`, `validaciones_identidad`; tabla `polizas_arrendamiento` no debe existir aún si es la primera corrida tras la migración)
- [x] 8.2 Correr los unit tests focalizados de `seguro-arrendamiento` vía `docker compose exec backend pytest tests/seguro_arrendamiento`
- [x] 8.3 Correr la suite completa vía `docker compose exec backend pytest`
- [x] 8.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [x] 8.5 Crear el reporte `openspec/changes/seguro-arrendamiento-inquilino/specs/reports/YYYY-MM-DD-step-8-unit-test-and-db-verification.md`
- [x] 8.6 Marcar este paso como completo solo después de que los tests pasen y el reporte exista

## 9. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 9.1 `docker compose up` con rebuild del backend tras la migración
- [x] 9.2 curl: `POST /seguro-arrendamiento/contratar` con documentos válidos (cuenta inquilino con identidad ya verificada) — verificar 200 y estado `aprobada` con `prima_mensual`
- [x] 9.3 curl: mismo endpoint con cuenta inquilino SIN identidad verificada — verificar rechazo explícito sin llamar al proveedor
- [x] 9.4 curl: payload inválido (sin documentos) — verificar 422
- [x] 9.5 Documentar los resultados en `openspec/changes/seguro-arrendamiento-inquilino/specs/reports/YYYY-MM-DD-step-9-manual-curl-testing.md`

## 10. Documentación (OBLIGATORIO)

- [x] 10.1 Actualizar `docs/architecture/architecture.md` con el nuevo dominio `backend/seguro-arrendamiento/`, su puerto/adapters, y la tabla `polizas_arrendamiento`
- [x] 10.2 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-005-analisis-riesgo-seguro-arrendamiento.md`, anotar que el mecanismo elegido es solo seguro (Sura) — resolviendo el punto abierto crítico del PRD — y que la firma electrónica queda fuera de alcance como HU propia futura
