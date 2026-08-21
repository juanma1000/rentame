# Reporte Paso 10 - Testing Manual de Endpoints con curl

- Fecha: 2026-08-19
- Cambio: hu-001
- Agente: backend-expert

## Preparación del Entorno

- Base de datos objetivo: **desarrollo** (`rentame`, `DATABASE_URL` en `backend/.env`), no `rentame_test`.
- Servidor: `uvicorn main:app --host 127.0.0.1 --port 8000` (reiniciado durante el testing, ver "Hallazgos" — logs en `/tmp/uvicorn.log`).
- Servicios: `rentame-postgres` y `rentame-minio` (docker-compose), ambos `Up (healthy)` antes de empezar.
- Usuarios de prueba: no existía ningún seed de `usuario` reutilizable, así que se insertaron 2 filas reales en la tabla `usuario` de `rentame` (rol `propietario`), y se emitió un JWT válido para cada una con el helper `tests/utils/auth.py::build_valid_token` (mismo emisor/algoritmo que usa la app real vía `shared/infrastructure/auth/jwt_handler.py`):
  - Propietario A (dueño): `d3ed2d1a-4d36-45d1-bad6-4fec6b87fa1a` (`propietario.a.hu001@rentame.test`) — usado para 10.2, 10.5, 10.7, 10.8.
  - Propietario B (no dueño): `9267407e-8b91-4eca-8c55-7471df35d1bd` (`propietario.b.hu001@rentame.test`) — usado para 10.6 y para confirmar aislamiento en 10.8.
  - Ambas filas de `usuario` se eliminaron al final (ver "Limpieza Final").
- Baseline pre-test verificado en `rentame`: `inmueble` = 0 filas, `foto_inmueble` = 0 filas, `usuario` = 0 filas, bucket MinIO `inmuebles` = 0 objetos.

## Hallazgos Críticos Encontrados y Corregidos Durante el Testing

El testing manual (a diferencia de los tests de integración, que comparten una única `AsyncSession` por test y por eso nunca lo detectaron) encontró **dos bugs reales que impedían que la app funcionara contra un servidor `uvicorn` real**:

### 1. `NoReferencedTableError` al arrancar `main.py` sin importar `usuarios`

`InmuebleORM.propietario_id`/`agente_id` (`inmuebles/infrastructure/persistence/models.py`) declaran `ForeignKey("usuario.id")`, pero `main.py` nunca importaba `usuarios.infrastructure.persistence.models.UsuarioORM`, así que ese mapper nunca se registraba en `Base.metadata` en el proceso de la app real (los tests sí lo hacen, vía `tests/conftest.py`). El primer intento de `POST /inmuebles/` (10.2) devolvió `500 Internal Server Error` con `sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'inmueble.propietario_id' could not find table 'usuario'`.

**Fix aplicado**: se agregó a `backend/main.py` el mismo import (con `# noqa: F401`) que `alembic/env.py` ya usaba por esta misma razón:
```python
from usuarios.infrastructure.persistence.models import UsuarioORM  # noqa: F401
```

### 2. `get_db_session()` nunca hacía `commit()` — ninguna escritura real persistía

Tras corregir (1), el mismo `POST` devolvió `201` con un `id` válido, pero una consulta directa a Postgres mostró `inmueble` count = 0: la fila nunca se persistió. `shared/infrastructure/database.py::get_db_session` hacía `async with AsyncSessionLocal() as session: yield session` sin `commit()` explícito, y `InmuebleRepositoryPostgres` (correctamente, por diseño) solo hace `flush()`, dejando el commit al llamador. Al cerrarse la sesión sin commit, la transacción se descartaba implícitamente — **todo `POST`/`PUT`/`PATCH` real habría devuelto una respuesta 2xx exitosa sin persistir nada**, en cualquier entorno real (dev/staging/prod). Los 55 tests existentes no lo detectan porque `test_api.py` sobrescribe `get_db_session` para que todos los requests de un test compartan la misma sesión/transacción no confirmada, y leen el dato recién `flush`eado dentro de esa misma transacción.

**Fix aplicado** en `shared/infrastructure/database.py`:
```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Verificación tras ambos fixes**:
- `python -m pytest -q` (suite completa): **55 passed, 0 failed** — sin regresiones (los tests de `test_api.py` no ejercitan esta rama porque sobrescriben la dependencia, por eso `database.py` queda en 56% de cobertura de líneas, esperado).
- Reintento de 10.2: `201`, y la fila quedó verificablemente persistida en `inmueble`/`foto_inmueble` vía consulta directa a Postgres.
- Se limpiaron 2 objetos huérfanos en MinIO que había dejado el intento fallido (500) previo al fix, antes de continuar con el resto de los casos.

Estos dos hallazgos son bloqueantes para cualquier entorno real y quedan documentados como "riesgo mitigado dentro de este mismo change" — no se abre un cambio aparte porque el fix es mínimo, acotado a infraestructura compartida ya tocada por `hu-001`, y quedó validado tanto por curl real como por la suite de tests.

## Comandos Ejecutados y Resultados

### 10.1 — Levantar el servidor y confirmar conexión a la base de datos

```bash
nohup ./.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &
curl -s http://localhost:8000/health
curl -s http://localhost:8000/openapi.json | python3 -c "import json,sys; print(list(json.load(sys.stdin)['paths'].keys()))"
```
Respuesta:
```
{"status":"ok"}
['/inmuebles/', '/inmuebles/{inmueble_id}', '/inmuebles/{inmueble_id}/disponibilidad', '/inmuebles/mios', '/health']
```
Servidor arriba, conectado a `rentame`, todas las rutas de `inmuebles` expuestas. PASS.

### 10.2 — `POST /inmuebles/` con datos y 1 foto válidos

```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/inmuebles/ \
  -H "Authorization: Bearer $TOKEN_A" \
  -F "direccion=Calle 10 # 20-30" -F "barrio=El Poblado" -F "ciudad=Medellin" \
  -F "tipo=apartamento" -F "area_m2=75.5" -F "habitaciones=2" -F "banos=2" \
  -F "valor_mensual=1500000" -F "descripcion=Apartamento de prueba para testing manual HU-001" \
  -F "fotos=@foto1.png;type=image/png"
```
Respuesta (`HTTP_STATUS:201`):
```json
{"id":"fd8119ec-7d80-452d-a2bc-0305224812b6","propietario_id":"d3ed2d1a-4d36-45d1-bad6-4fec6b87fa1a","direccion":"Calle 10 # 20-30","barrio":"El Poblado","ciudad":"Medellin","tipo":"apartamento","area_m2":75.5,"habitaciones":2,"banos":2,"valor_mensual":1500000.0,"descripcion":"Apartamento de prueba para testing manual HU-001","estado":"disponible","fotos":[{"url_storage":"http://localhost:9000/inmuebles/inmuebles/a85bed13-.../a3f139a1-....jpg","storage_key":"inmuebles/a85bed13-.../a3f139a1-....jpg","orden":1,"es_principal":true}]}
```
`201`, `estado: disponible`. Verificado con consulta directa a Postgres (`inmueble` count pasó de 0 a 1, `foto_inmueble` de 0 a 1) y a MinIO (1 objeto subido). Este registro se reutilizó para 10.5-10.8 y se eliminó en la limpieza final (ver abajo). PASS.

### 10.3 — `POST /inmuebles/` sin fotos

```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/inmuebles/ \
  -H "Authorization: Bearer $TOKEN_A" \
  -F "direccion=..." -F "barrio=..." -F "ciudad=..." -F "tipo=apartamento" \
  -F "area_m2=75.5" -F "habitaciones=2" -F "banos=2" -F "valor_mensual=1500000" \
  -F "descripcion=Apartamento sin fotos - test 10.3"
```
Respuesta (`HTTP_STATUS:422`):
```json
{"detail":[{"type":"missing","loc":["body","fotos"],"msg":"Field required","input":null}]}
```
`422` (validación propia de FastAPI, ya que el campo `fotos` está completamente ausente del multipart — el caso "0 fotos adjuntas pero campo presente" lo cubre la validación de dominio, ejercitada por `test_api.py`). Se confirmó que `inmueble`/`foto_inmueble`/MinIO quedaron sin cambios (1/1/1, igual que tras 10.2). PASS.

### 10.4 — `POST /inmuebles/` con 11 fotos

```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/inmuebles/ \
  -H "Authorization: Bearer $TOKEN_A" \
  -F "direccion=..." [...] -F "descripcion=Apartamento con 11 fotos - test 10.4" \
  -F fotos=@foto1.png;type=image/png [x11]
```
Respuesta (`HTTP_STATUS:422`):
```json
{"detail":"fotos count must be between 1 and 10, got 11"}
```
`422` con mensaje de dominio. Se confirmó explícitamente que **no quedaron objetos huérfanos en MinIO**: el bucket siguió con exactamente 1 objeto (el de 10.2, aún vigente), ninguna de las 11 fotos del intento rechazado quedó subida — consistente con el fix de "no huérfanos" mencionado en la tarea. PASS.

### 10.5 — `PUT /inmuebles/{id}` como dueño

```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X PUT http://localhost:8000/inmuebles/fd8119ec-.../ \
  -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" \
  -d '{"direccion":"Carrera 45 # 12-08","barrio":"Laureles","ciudad":"Medellin","tipo":"apartamento","area_m2":82.0,"habitaciones":3,"banos":2,"valor_mensual":1800000,"descripcion":"Descripcion actualizada - test 10.5"}'
```
Respuesta (`HTTP_STATUS:200`): body con todos los campos actualizados (`direccion: "Carrera 45 # 12-08"`, `valor_mensual: 1800000.0`, etc.), `estado` sin cambios (`disponible`). Confirmado también vía `GET /inmuebles/mios`. PASS. Valores originales restaurados al final del testing (ver "Limpieza Final").

### 10.6 — `PUT /inmuebles/{id}` como otro propietario

```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X PUT http://localhost:8000/inmuebles/fd8119ec-.../ \
  -H "Authorization: Bearer $TOKEN_B" -H "Content-Type: application/json" \
  -d '{"direccion":"Intento hostil", [...] "descripcion":"No deberia poder - test 10.6"}'
```
Respuesta (`HTTP_STATUS:403`):
```json
{"detail":"Propietario 9267407e-8b91-4eca-8c55-7471df35d1bd no es dueño del inmueble fd8119ec-7d80-452d-a2bc-0305224812b6"}
```
`403` (no `404`, correcto por diseño: la spec exige distinguir "no soy el dueño" de "no existe"). Se confirmó con un `GET /inmuebles/mios` posterior (propietario A) que el registro **no fue mutado** por el intento — siguen los valores de 10.5. PASS.

### 10.7 — `PATCH /inmuebles/{id}/disponibilidad` despublicar y republicar

Despublicar:
```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X PATCH http://localhost:8000/inmuebles/fd8119ec-.../disponibilidad \
  -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" \
  -d '{"nuevo_estado":"oculto"}'
```
Respuesta (`HTTP_STATUS:200`): `"estado":"oculto"` (resto de campos sin cambios).

Republicar:
```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X PATCH http://localhost:8000/inmuebles/fd8119ec-.../disponibilidad \
  -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" \
  -d '{"nuevo_estado":"disponible"}'
```
Respuesta (`HTTP_STATUS:200`): `"estado":"disponible"`. Ambas transiciones correctas. PASS.

### 10.8 — `GET /inmuebles/mios` con JWT del propietario

Propietario A (dueño del inmueble de prueba):
```bash
curl -s http://localhost:8000/inmuebles/mios -H "Authorization: Bearer $TOKEN_A"
```
Respuesta (`HTTP_STATUS:200`): array con exactamente 1 elemento — el inmueble de prueba, con sus datos actualizados por 10.5 y `estado: disponible` (post-10.7).

Propietario B (sin inmuebles propios):
```bash
curl -s -w "\nHTTP_STATUS:%{http_code}\n" http://localhost:8000/inmuebles/mios -H "Authorization: Bearer $TOKEN_B"
```
Respuesta (`HTTP_STATUS:200`): `[]`.

Confirma aislamiento correcto por `propietario_id`. PASS.

## Limpieza Final (Restauración de Estado)

1. `PUT /inmuebles/{id}` como propietario A con los valores originales de 10.2 (`direccion`, `barrio`, `ciudad`, `tipo`, `area_m2`, `habitaciones`, `banos`, `valor_mensual`, `descripcion`) → `200`, valores restaurados.
2. Eliminado el objeto de MinIO `inmuebles/a85bed13-.../a3f139a1-....jpg` (foto del inmueble de prueba) vía `boto3.delete_object`.
3. `DELETE FROM inmueble WHERE id = 'fd8119ec-...'` en `rentame` (cascada a `foto_inmueble` por `ondelete="CASCADE"`) → 1 fila eliminada.
4. `DELETE FROM usuario WHERE email IN ('propietario.a.hu001@rentame.test', 'propietario.b.hu001@rentame.test')` → 2 filas eliminadas.

## Verificación de Estado de Base de Datos Post-Limpieza

- `inmueble`: 0 filas (baseline: 0) ✔
- `foto_inmueble`: 0 filas (baseline: 0) ✔
- `usuario`: 0 filas (baseline: 0) ✔
- Bucket MinIO `inmuebles`: 0 objetos (baseline: 0) ✔
- Suite completa de tests (`pytest -q`) tras aplicar los dos fixes: **55 passed, 0 failed** — sin regresiones.

Estado de la base de datos de desarrollo idéntico al pre-test. Servidor `uvicorn` se dejó corriendo (con los fixes aplicados) para uso posterior del equipo.

## Resultado

- Estado del Paso 10: **PASS**
- Issues bloqueantes: ninguno (los 2 bugs críticos encontrados durante el testing — importación faltante de `UsuarioORM` en `main.py`, y falta de `commit()` en `get_db_session` — fueron corregidos y verificados dentro de este mismo paso, con suite de tests en verde tras el fix).
- Archivos modificados como parte de este paso: `backend/main.py`, `backend/shared/infrastructure/database.py`.
