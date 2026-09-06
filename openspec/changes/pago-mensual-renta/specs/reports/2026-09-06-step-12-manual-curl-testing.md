# Reporte Paso 12 - Testing Manual de Endpoints con curl

- Fecha: 2026-09-06
- Cambio: pago-mensual-renta
- Agente: qa-expert (Claude Code)

`docker compose ps` confirmó los 5 servicios up (`rentame-backend` con bind mount + `--reload`, sirve código actual sin rebuild necesario tras la migración de `pagos` ya aplicada en la sección 6). `docker compose exec backend alembic current` confirmó `d4e5f6a7b8c9 (head)`. Todos los comandos se ejecutaron desde el host contra `http://localhost:8000`, con Postgres real (DB `rentame`). Baseline pre-test: `usuario`=12, `validaciones_identidad`=0, `polizas_arrendamiento`=0, `contratos`=0, `arrendamientos_activos`=0, `pagos`=0, `inmueble`=7.

Nota sobre `generar_pagos_del_ciclo`: el agente anterior lo expuso solo como script standalone (`backend/scripts/generar_pagos_mensuales.py`), invocado con `docker compose exec backend python scripts/generar_pagos_mensuales.py` — no hay endpoint HTTP para dispararlo (consistente con design.md: tarea ECS/Fargate one-off, nunca un scheduler embebido en la app). La primera invocación falló con `ModuleNotFoundError: No module named 'pagos'` porque `python scripts/generar_pagos_mensuales.py` antepone el directorio `scripts/` (no `/app`) a `sys.path`; se resolvió invocando con `docker compose exec -e PYTHONPATH=/app backend python scripts/generar_pagos_mensuales.py`.

**Este no es solo un detalle de invocación manual: es el mismo comando que corre la tarea ECS real.** `infra/aws/pagos-mensuales-task/main.tf` (línea 94) define `command = ["python", "scripts/generar_pagos_mensuales.py"]`, sin ninguna variable `PYTHONPATH` en el mismo archivo ni en `backend/Dockerfile`/`backend/docker-entrypoint.sh` (que solo hace `alembic upgrade head` condicional y luego `exec "$@"`, sin fijar `PYTHONPATH`). Confirmado leyendo los tres archivos: el `WORKDIR /app` del Dockerfile hace que `uvicorn main:app` (el `CMD` por defecto) funcione porque el propio `uvicorn` agrega el cwd a `sys.path`, pero `python scripts/generar_pagos_mensuales.py` invocado directamente **no** hace lo mismo — antepone el directorio del script (`/app/scripts`), no `/app`. Con la configuración actual de `infra/aws/pagos-mensuales-task/main.tf`, la tarea ECS real fallaría en producción con el mismo `ModuleNotFoundError: No module named 'pagos'` reproducido acá. Esto pertenece a las tareas 9.1/9.3 (ya marcadas completas, fuera de mi alcance en las secciones 10-12), pero se documenta como hallazgo bloqueante para que se corrija antes de desplegar el job mensual — por ejemplo agregando `{ name = "PYTHONPATH", value = "/app" }` a las variables de entorno de la tarea en `main.tf`, o cambiando el `command` a `["python", "-m", "scripts.generar_pagos_mensuales"]` (requiere que `scripts/` tenga `__init__.py`, a confirmar).

Nota sobre `FakeAdapter` (adapter activo por default en este ambiente, confirmado por `infrastructure/proveedor.py`): a diferencia de Wompi real, `FakeAdapter.iniciar_cobro` siempre retorna `estado="completado"` de forma síncrona — por lo tanto `POST /pagos/{id}/iniciar` deja el `Pago` ya `completado` en la misma llamada, sin pasar nunca por un estado intermedio que dependa de `POST /pagos/webhook`. Para poder ejercitar el endpoint de webhook de forma aislada (tarea 12.5) se preparó manualmente, vía `UPDATE` directo en la tabla `pagos`, un segundo `Pago` `pendiente` con `referencia_externa` ya asignada — simulando el estado en el que quedaría un `Pago` tras un `iniciar_cobro` asíncrono real de Wompi (mismo escenario que ejercita el test automatizado `tests/pagos/infrastructure/test_api.py::TestWebhookPagoEndpoint`, que construye el fixture de la misma manera).

## 1. Preparación: propietario + inmueble + inquilino con identidad y póliza aprobada

```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.propietario.pagos@rentame.test","password":"Secreta123!","nombre":"Curl Propietario Pagos","rol":"propietario"}'
```
→ `propietario.id=f414efec-5859-4ac3-9c4c-bf58bfa1a5e3` (guardado como `$PROP_TOKEN`).

```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino.pagos@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino Pagos","rol":"inquilino"}'
```
→ `inquilino.id=7cdb8837-8864-446c-af98-c3631c0cb3d1` (guardado como `$INQ_TOKEN`).

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $INQ_TOKEN" \
  -F "cedula=6001112233" -F "imagen_frente=@/tmp/frente.jpg" -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `200` — `{"id":"c382f944-29ef-4fc7-bdba-c0ce8fb449e1","estado":"aprobado","referencia_externa":"FAKE-e40c932e506dfdbc"}`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/seguro-arrendamiento/contratar \
  -H "Authorization: Bearer $INQ_TOKEN" \
  -F "cedula=6001112233" -F "documentos=@/tmp/frente.jpg" -F "documentos=@/tmp/dorso.jpg"
```
→ `200` — `{"id":"f6639521-5dd3-4195-a312-a8ce5f769e50","estado":"aprobada","prima_mensual":45000.0,"referencia_externa":"FAKE-e40c932e506dfdbc"}`

Un `Inmueble` real es necesario porque, a diferencia del flujo de `firma_contrato` (que acepta cualquier UUID arbitrario como `inmueble_id`), `pagos.infrastructure.persistence.inmueble_repository.InmuebleRepositoryPostgres.obtener` hace un `session.get(InmuebleORM, inmueble_id)` real — tanto `generar_pagos_del_ciclo` (lee `valor_mensual`) como `iniciar_pago` (lee `propietario_id` para el split) necesitan que exista la fila:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/inmuebles/ \
  -H "Authorization: Bearer $PROP_TOKEN" \
  -F "direccion=Calle Pagos 100" -F "barrio=Centro" -F "ciudad=Bogota" -F "tipo=apartamento" \
  -F "area_m2=60" -F "habitaciones=2" -F "banos=1" -F "valor_mensual=1500000" \
  -F "descripcion=Inmueble de prueba para curl pagos" -F "fotos=@/tmp/foto1.jpg"
```
→ `201` — `inmueble.id=ef465ef9-3617-41bd-b490-acd5fd9079b7`, `propietario_id=f414efec-5859-4ac3-9c4c-bf58bfa1a5e3`, `valor_mensual=1500000.0`.

## 2. Cadena hasta `ArrendamientoActivo`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/generar \
  -H "Authorization: Bearer $INQ_TOKEN" -H "Content-Type: application/json" \
  -d '{"inmueble_id":"ef465ef9-3617-41bd-b490-acd5fd9079b7","nombre_inquilino":"Curl Inquilino Pagos","nombre_propietario":"Curl Propietario Pagos","direccion_inmueble":"Calle Pagos 100","canon_mensual":1500000,"duracion_meses":12}'
```
→ `200` — `{"id":"6dd12870-42f6-4120-9c5d-b7233587b52c","estado":"enviado_a_firma","referencia_externa":"FAKE-e8417f3229ed8803"}`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/webhook \
  -H "Content-Type: application/json" \
  -d '{"referencia_externa":"FAKE-e8417f3229ed8803","estado":"firmado"}'
```
→ `200` — `{"id":"6dd12870-42f6-4120-9c5d-b7233587b52c","estado":"firmado","referencia_externa":"FAKE-e8417f3229ed8803"}`

Verificación directa:
```sql
SELECT id, usuario_id, contrato_id, inmueble_id, estado FROM arrendamientos_activos WHERE contrato_id='6dd12870-42f6-4120-9c5d-b7233587b52c';
```
→ `id=e21544c3-799c-45c3-83f3-8a1fe2333da1 | usuario_id=7cdb8837-8864-446c-af98-c3631c0cb3d1 | contrato_id=6dd12870-42f6-4120-9c5d-b7233587b52c | inmueble_id=ef465ef9-3617-41bd-b490-acd5fd9079b7 | estado=activo`

## 3. `generar_pagos_del_ciclo` (job manual) crea un `Pago` pendiente (tarea 12.2)

```
docker compose exec -e PYTHONPATH=/app backend python scripts/generar_pagos_mensuales.py
```
→ log: `generar_pagos_del_ciclo: 1 Pago(s) pendiente(s) creado(s)`

Verificación directa:
```sql
SELECT id, arrendamiento_activo_id, estado, monto, fecha_limite, fecha_pago, referencia_externa FROM pagos WHERE arrendamiento_activo_id='e21544c3-799c-45c3-83f3-8a1fe2333da1';
```
→ `id=2bbb69d7-7e92-4f6a-824d-b1c00d161e12 | estado=pendiente | monto=1500000.00 | fecha_limite=2026-09-11 | fecha_pago=NULL | referencia_externa=NULL`
(`monto` = `Inmueble.valor_mensual`, `fecha_limite` = hoy + 5 días, per `DIAS_PLAZO_PAGO` en `generar_pagos_del_ciclo.py`)

## 4. Segunda corrida del job — idempotencia (tarea 12.3)

```
docker compose exec -e PYTHONPATH=/app backend python scripts/generar_pagos_mensuales.py
```
→ log: `generar_pagos_del_ciclo: 0 Pago(s) pendiente(s) creado(s)`

```sql
SELECT id, arrendamiento_activo_id, estado FROM pagos WHERE arrendamiento_activo_id='e21544c3-799c-45c3-83f3-8a1fe2333da1';
```
→ sigue habiendo una única fila (`2bbb69d7-7e92-4f6a-824d-b1c00d161e12 | pendiente`) — confirmado: no se creó un segundo `Pago` pendiente para el mismo `ArrendamientoActivo`/ciclo.

## 5. `POST /pagos/{id}/iniciar` sobre el pago pendiente (tarea 12.4)

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/pagos/2bbb69d7-7e92-4f6a-824d-b1c00d161e12/iniciar \
  -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200`
```json
{"id":"2bbb69d7-7e92-4f6a-824d-b1c00d161e12","arrendamiento_activo_id":"e21544c3-799c-45c3-83f3-8a1fe2333da1","estado":"completado","monto":1500000.0,"fecha_limite":"2026-09-11","fecha_pago":"2026-09-06T18:19:03.957804Z","referencia_externa":"FAKE-7c52d0de4d72ac0e"}
```
Con `FakeAdapter` el pago queda `completado` de inmediato (ver nota arriba). Verificación directa:
```sql
SELECT id, estado, fecha_pago, referencia_externa FROM pagos WHERE id='2bbb69d7-7e92-4f6a-824d-b1c00d161e12';
```
→ `estado=completado | fecha_pago=2026-09-06 18:19:03.957804+00 | referencia_externa=FAKE-7c52d0de4d72ac0e`

Casos de error del mismo endpoint, verificados también:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/pagos/00000000-0000-0000-0000-000000000000/iniciar -H "Authorization: Bearer $INQ_TOKEN"
```
→ `404` — `{"detail":"No existe ningún Pago con id=00000000-0000-0000-0000-000000000000"}`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/pagos/2bbb69d7-7e92-4f6a-824d-b1c00d161e12/iniciar -H "Authorization: Bearer $INQ_TOKEN"
```
(sobre el mismo pago, ya `completado`) → `409` — `{"detail":"El pago 2bbb69d7-7e92-4f6a-824d-b1c00d161e12 ya está completado y no puede reiniciarse"}`

## 6. `POST /pagos/webhook` — resultado `completado` (tarea 12.5)

Como el pago anterior ya quedó `completado` (no unresolved), se corrió el job una tercera vez para generar un segundo `Pago` `pendiente` sobre el mismo `ArrendamientoActivo` (confirma además que la idempotencia solo bloquea mientras exista un pendiente sin resolver — un pago ya completado no impide generar uno nuevo para el siguiente ciclo):
```
docker compose exec -e PYTHONPATH=/app backend python scripts/generar_pagos_mensuales.py
```
→ log: `generar_pagos_del_ciclo: 1 Pago(s) pendiente(s) creado(s)` → nuevo `Pago` `6d32dc80-da60-4751-95e4-1ff65df42831`, `pendiente`.

Se simuló manualmente el estado intermedio de un cobro Wompi en curso (referencia_externa asignada, aún pendiente — mismo escenario del fixture del test automatizado):
```sql
UPDATE pagos SET referencia_externa='FAKE-WEBHOOK-TEST-1234' WHERE id='6d32dc80-da60-4751-95e4-1ff65df42831';
```

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/pagos/webhook \
  -H "Content-Type: application/json" \
  -d '{"referencia_externa":"FAKE-WEBHOOK-TEST-1234","estado":"completado"}'
```
→ `200`
```json
{"id":"6d32dc80-da60-4751-95e4-1ff65df42831","arrendamiento_activo_id":"e21544c3-799c-45c3-83f3-8a1fe2333da1","estado":"completado","monto":1500000.0,"fecha_limite":"2026-09-11","fecha_pago":"2026-09-06T18:19:34.108717Z","referencia_externa":"FAKE-WEBHOOK-TEST-1234"}
```

Verificación directa:
```sql
SELECT id, estado, fecha_pago, referencia_externa FROM pagos WHERE id='6d32dc80-da60-4751-95e4-1ff65df42831';
```
→ `estado=completado | fecha_pago=2026-09-06 18:19:34.108717+00 | referencia_externa=FAKE-WEBHOOK-TEST-1234` — confirmado: el `Pago` queda `completado` con `fecha_pago` seteada, tal como exige la tarea 12.5.

## 7. `GET /arrendamientos/{id}/pagos` — historial (tarea 12.6)

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/arrendamientos/e21544c3-799c-45c3-83f3-8a1fe2333da1/pagos \
  -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200`
```json
{"pagos":[
  {"id":"2bbb69d7-7e92-4f6a-824d-b1c00d161e12","estado":"completado","monto":1500000.0,"fecha_limite":"2026-09-11","fecha_pago":"2026-09-06T18:19:03.957804Z","referencia_externa":"FAKE-7c52d0de4d72ac0e"},
  {"id":"6d32dc80-da60-4751-95e4-1ff65df42831","estado":"completado","monto":1500000.0,"fecha_limite":"2026-09-11","fecha_pago":"2026-09-06T18:19:34.108717Z","referencia_externa":"FAKE-WEBHOOK-TEST-1234"}
]}
```
Ambos `Pago`s del `ArrendamientoActivo` aparecen en el historial, confirmando la tarea 12.6.

## Restauración de la base de datos

```sql
DELETE FROM pagos WHERE arrendamiento_activo_id='e21544c3-799c-45c3-83f3-8a1fe2333da1';
DELETE FROM arrendamientos_activos WHERE id='e21544c3-799c-45c3-83f3-8a1fe2333da1';
DELETE FROM contratos WHERE id='6dd12870-42f6-4120-9c5d-b7233587b52c';
DELETE FROM foto_inmueble WHERE inmueble_id='ef465ef9-3617-41bd-b490-acd5fd9079b7';
DELETE FROM inmueble WHERE id='ef465ef9-3617-41bd-b490-acd5fd9079b7';
DELETE FROM polizas_arrendamiento WHERE usuario_id IN (SELECT id FROM usuario WHERE email IN ('curl.propietario.pagos@rentame.test','curl.inquilino.pagos@rentame.test'));
DELETE FROM validaciones_identidad WHERE usuario_id IN (SELECT id FROM usuario WHERE email IN ('curl.propietario.pagos@rentame.test','curl.inquilino.pagos@rentame.test'));
DELETE FROM usuario WHERE email IN ('curl.propietario.pagos@rentame.test','curl.inquilino.pagos@rentame.test');
```
Conteos post-limpieza (DB `rentame`): `usuario`=12, `validaciones_identidad`=0, `polizas_arrendamiento`=0, `contratos`=0, `arrendamientos_activos`=0, `pagos`=0, `inmueble`=7 — idénticos al baseline pre-test.

Nota: el objeto de la foto subida a MinIO (`inmuebles/2f6c21cb-.../f163bbd3-....jpg`) no fue borrado del bucket — la fila de `foto_inmueble` que lo referenciaba en Postgres sí fue eliminada arriba. Inofensivo: es un objeto huérfano en un bucket de desarrollo local (MinIO), sin ninguna fila en la base de datos que lo referencie ni ningún proceso que lo liste por convención de nombre.

## Resultado
- Estado del Paso 12 (secciones 12 de `tasks.md`, mi alcance): PASS — toda la cadena de endpoints se ejerció con éxito manualmente (con el workaround de `PYTHONPATH` documentado arriba para invocar el script).
- Issue bloqueante encontrado, fuera de mi alcance de sección (10-12) pero perteneciente a tareas 9.1/9.3 ya marcadas completas: **la tarea ECS/Fargate del job mensual (`infra/aws/pagos-mensuales-task/main.tf`, `command = ["python", "scripts/generar_pagos_mensuales.py"]`) fallaría en producción con `ModuleNotFoundError: No module named 'pagos'`**, por la misma razón reproducida en este reporte — no hay `PYTHONPATH=/app` (ni equivalente) configurado en ningún lado de la cadena Dockerfile/entrypoint/Terraform. Se recomienda que `backend-expert` corrija `infra/aws/pagos-mensuales-task/main.tf` antes de considerar cerrado el change completo (afecta directamente el único mecanismo de producción del job mensual, no solo el testing manual).
