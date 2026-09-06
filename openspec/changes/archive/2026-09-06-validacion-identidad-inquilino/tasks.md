## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/validacion-identidad-inquilino` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: dominio `identidad` — aggregate y puerto

- [x] 1.1 qa-expert (Red): tests unitarios de `ValidacionIdentidad` — creación, estados (`pendiente`/`aprobado`/`rechazado`), invariante de "una sola validación aprobada por cuenta"
- [x] 1.2 backend-expert (Green): `backend/identidad/domain/validacion_identidad.py` (aggregate `ValidacionIdentidad`)
- [x] 1.3 backend-expert: `backend/identidad/domain/ports.py` — `ProveedorValidacionIdentidadPort` (interfaz `validar(cedula, imagen_frente, imagen_dorso) -> ResultadoValidacion`)
- [x] 1.4 backend-expert: `backend/identidad/domain/exceptions.py` (ej. `CuentaYaVerificadaError`)

## 2. Backend: `FakeAdapter` para dev/test

- [x] 2.1 qa-expert (Red): test de `FakeAdapter.validar(...)` — siempre retorna `aprobado` con `referencia_externa` determinística
- [x] 2.2 backend-expert (Green): `backend/identidad/infrastructure/adapters/fake_adapter.py`

## 3. Backend: caso de uso `iniciar_validacion_identidad`

- [x] 3.1 qa-expert (Red): tests con `FakeAdapter` inyectado — validación aprobada marca `Usuario.identidad_verificada = True`; segundo intento sobre cuenta ya verificada se rechaza sin llamar al proveedor
- [x] 3.2 qa-expert (Red): test con stub propio del puerto (no el `FakeAdapter` compartido) simulando rechazo — persiste el intento, `identidad_verificada` permanece `False`
- [x] 3.3 backend-expert (Green): `backend/identidad/application/iniciar_validacion_identidad.py`

## 4. Backend: persistencia

- [x] 4.1 qa-expert (Red): test de integración de `ValidacionIdentidadRepositoryPostgres` contra Postgres real — crear, listar por `usuario_id`
- [x] 4.2 backend-expert (Green): `backend/identidad/infrastructure/persistence/models.py` + `repository.py` (tabla `validaciones_identidad`)
- [x] 4.3 backend-expert: migración Alembic — tabla `validaciones_identidad` (usuario_id FK, cedula, estado, fecha, referencia_externa) + columna `identidad_verificada BOOLEAN NOT NULL DEFAULT FALSE` en `usuarios`
- [x] 4.4 backend-expert: agregar `identidad_verificada: bool = False` a `backend/usuarios/domain/usuario.py` y mapear en `usuarios/infrastructure/persistence/models.py`

## 5. Backend: endpoint proxy

- [x] 5.1 qa-expert (Red): tests de integración `POST /identidad/validar` — payload válido (cédula + imágenes) retorna 200 con estado esperado; payload sin cédula o sin imágenes retorna 422; cuenta ya verificada retorna error explícito sin llamar al proveedor
- [x] 5.2 qa-expert (Red): test explícito que verifica que los bytes de imagen NO quedan persistidos en ninguna tabla/archivo tras la llamada
- [x] 5.3 backend-expert (Green): `backend/identidad/infrastructure/api/router.py` + `schemas.py` — recibe multipart (cédula + imagen frente/dorso), reenvía al puerto, descarta bytes tras la respuesta

## 6. Backend: `TruoraAdapter` (adapter real)

- [x] 6.1 qa-expert (Red): tests con HTTP client mockeado — mapeo correcto de respuesta Truora a `ResultadoValidacion`; manejo explícito de timeout/error de la API externa (no 500, estado claro de "validación no disponible")
- [x] 6.2 backend-expert (Green): `backend/identidad/infrastructure/adapters/truora_adapter.py`
- [x] 6.3 backend-expert: configuración por ambiente para seleccionar `FakeAdapter` (default) vs `TruoraAdapter` (prod, requiere credenciales configuradas)

## 7. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 7.1 Revisar suite completa de `backend/tests/` en busca de fixtures/tests afectados por la nueva columna `identidad_verificada` en `usuarios` — actualizar fixtures de `Usuario` si algún test construye instancias con argumentos posicionales
- [x] 7.2 Confirmar que ningún test existente de `usuarios`/`agencias`/`inmuebles` se rompe por el cambio aditivo

## 8. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 8.1 Capturar el baseline de base de datos pre-test (conteo de filas en `usuario`, tabla `validaciones_identidad` en 0 filas)
- [x] 8.2 Correr los unit tests focalizados de `identidad` vía `docker compose exec backend pytest tests/identidad` (30 passed)
- [x] 8.3 Correr la suite completa vía `docker compose exec backend pytest` (250 passed)
- [x] 8.4 Verificar el estado post-test de la base de datos y restaurar si hace falta (sin mutaciones, no fue necesaria restauración)
- [x] 8.5 Crear el reporte `openspec/changes/validacion-identidad-inquilino/specs/reports/2026-09-06-step-8-unit-test-and-db-verification.md`
- [x] 8.6 Marcar este paso como completo solo después de que los tests pasen y el reporte exista

## 9. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 9.1 `docker compose up` con rebuild del backend tras la migración (backend ya corriendo con bind mount + `--reload`; migración `a1b2c3d4e5f6 (head)` confirmada aplicada vía `alembic current`)
- [x] 9.2 curl: `POST /identidad/validar` con cédula + imágenes válidas (cuenta inquilino de prueba) — verificar 200 y `identidad_verificada = True` tras consultar el perfil (verificado directo en Postgres, no hay endpoint GET de perfil)
- [x] 9.3 curl: segundo intento sobre la misma cuenta — verificar rechazo explícito (409) sin nueva llamada al proveedor (confirmado: sin fila nueva en `validaciones_identidad`)
- [x] 9.4 curl: payload inválido (sin cédula/imágenes) — verificar 422
- [x] 9.5 Documentar los resultados en `openspec/changes/validacion-identidad-inquilino/specs/reports/2026-09-06-step-9-manual-curl-testing.md`

## 10. Documentación (OBLIGATORIO)

- [x] 10.1 Actualizar `docs/architecture/architecture.md` con el nuevo dominio `backend/identidad/`, su puerto/adapters, y la columna nueva en `usuarios`
- [x] 10.2 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-004-validacion-identidad-inquilino.md`, y anotar que el proveedor elegido es Truora (resolviendo el punto abierto del PRD)
