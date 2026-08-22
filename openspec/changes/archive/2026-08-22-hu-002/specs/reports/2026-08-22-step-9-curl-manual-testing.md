# Reporte Paso 9 - Testing Manual de Endpoints con curl

- Fecha: 2026-08-22
- Cambio: hu-002
- Agente: qa-expert (Claude Sonnet 5)

## Entorno

- Backend dockerizado (`rentame-backend`, bind mount + `--reload`) ya corriendo en `http://localhost:8000` antes de empezar (no fue necesario `docker compose up`).
- `curl -s -w "\nHTTP_STATUS:%{http_code}\n" http://localhost:8000/health` → `{"status":"ok"}` / `HTTP_STATUS:200`.
- Base de datos: Postgres real (`rentame`, servicio `postgres`), sin base de datos de test aislada para este paso (a diferencia del paso 8, que usa `rentame_test` para los tests automatizados).

## Baseline de Base de Datos (pre-test)

```
inmueble | usuario | agencia | relacion | solicitud | foto
---------+---------+---------+----------+-----------+-----
       0 |       1 |       0 |        0 |         0 |    0
```

(El único `usuario` preexistente ya estaba presente antes de este paso — no se tocó.)

## Preparación de Datos (vía API, no SQL directo salvo la creación de usuarios)

No existe endpoint de registro de usuarios en este backlog (`usuarios/infrastructure/persistence/models.py` documenta explícitamente que el registro está fuera de alcance hasta una futura HU de auth). Por lo tanto, los 4 usuarios de prueba se insertaron directamente en la tabla `usuario` (única excepción admitida, documentada en las instrucciones de este paso), y los JWT se emitieron con `create_access_token` del propio backend:

```sql
INSERT INTO usuario (id, email, rol) VALUES
  (gen_random_uuid(), 'maria.hu002.qa@test.local', 'propietario'),
  (gen_random_uuid(), 'agenteA.hu002.qa@test.local', 'agente'),
  (gen_random_uuid(), 'agenteB.hu002.qa@test.local', 'agente'),
  (gen_random_uuid(), 'agenteC.hu002.qa@test.local', 'agente')
RETURNING email, id;
```

IDs resultantes:
- María (propietario): `b9b4a520-3c09-444c-afe2-8fb15136026e`
- Agente A: `610141d9-fd7c-43ef-8c73-72fb4c9c4d73`
- Agente B: `db0f7c41-0b7f-4988-9e5e-20096d52d367`
- Agente C: `a567f3e8-0bde-4126-8d86-2d933be96914`

```
docker compose exec -T backend python -c "
from shared.infrastructure.auth.jwt_handler import create_access_token
print(create_access_token('<id>', '<rol>'))
"
```
→ un JWT por usuario (María: rol `propietario`; A/B/C: rol `agente`).

Todo el resto del setup se hizo vía la API real (endpoints de `agencias`, ya implementados por HU-007):

1. **Agente A crea su agencia** — `POST /agencias/` (JWT de A) → `201`, `agencia_id = bef7248d-6ea3-4768-b5bf-3ca58d7d6079`.
2. **Agente C crea su propia agencia** (distinta) — `POST /agencias/` (JWT de C) → `201`, `agencia_id = 4af745fc-dc9f-42c0-a05c-ae7652e73669`.
3. **Agente B solicita unirse a la agencia de A** — `POST /agencias/{agencia_A}/solicitudes` (JWT de B) → `201`, `estado: "pendiente"`, `solicitud_id = 734df0ce-c6d2-44b5-9a3c-2a249a1b39e7`.
4. **Agente A aprueba a B** — `POST /agencias/solicitudes/{solicitud_id}/aprobar` (JWT de A) → `200`, `estado: "aprobada"`. A y B quedan en la misma agencia.
5. **María inicia relación con la agencia de A/B** — `POST /agencias/{agencia_A}/relaciones` (JWT de María) → `201`, `estado: "pendiente"`, `relacion_id = 801c1e1d-cbd2-455b-ab30-377aedd249e4`.
6. **Agente A confirma la relación** — `POST /agencias/relaciones/{relacion_id}/confirmar` (JWT de A) → `200`, `estado: "activa"`.

Este setup deja exactamente la topología pedida: A y B en la misma agencia con relación `activa` con María; C en otra agencia, sin relación con María.

## Tests Ejecutados

### 9.2 — Agente A publica un inmueble para María (`propietario_id` en el form)

```
curl -X POST http://localhost:8000/inmuebles/ \
  -H "Authorization: Bearer <AGENTEA_JWT>" \
  -F "direccion=Calle 10 # 20-30" -F "barrio=El Poblado" -F "ciudad=Medellin" \
  -F "tipo=apartamento" -F "area_m2=80.5" -F "habitaciones=3" -F "banos=2" \
  -F "valor_mensual=1500000" -F "descripcion=Inmueble de prueba HU-002 Grupo 9" \
  -F "propietario_id=<MARIA_ID>" -F "fotos=@foto1.jpg;type=image/jpeg"
```

- **Resultado**: `HTTP_STATUS:201`.
- Body: `propietario_id = b9b4a520-...` (María), `agente_id = 610141d9-...` (Agente A), `estado: "disponible"`, 1 foto subida a MinIO (`storage_key: inmuebles/1398ec55-.../4ba7afd2-....jpg`).
- `inmueble_id = 493dac55-c463-4b91-a7a2-88072315d0ab`.
- **Esperado vs obtenido**: coincide — 201, `agente_id` es el de Agente A.

### 9.3 — Agente C intenta publicar para María (sin relación activa)

```
curl -X POST http://localhost:8000/inmuebles/ \
  -H "Authorization: Bearer <AGENTEC_JWT>" \
  -F "direccion=Calle 99 # 1-1" ... -F "propietario_id=<MARIA_ID>" -F "fotos=@foto1.jpg;type=image/jpeg"
```

- **Resultado**: `HTTP_STATUS:403`, `{"detail":"El agente no tiene una relación activa con este propietario"}`.
- Confirmado que la validación ocurre antes de leer/subir la foto (ningún inmueble ni foto quedó creado por este request).
- **Esperado vs obtenido**: coincide — 403.

### 9.4 — Agente B (misma agencia que A, no publicó) edita el inmueble

```
curl -X PUT http://localhost:8000/inmuebles/<inmueble_id> \
  -H "Authorization: Bearer <AGENTEB_JWT>" -H "Content-Type: application/json" \
  -d '{"direccion":"Calle 10 # 20-30 (editado por Agente B)", ... }'
```

- **Resultado**: `HTTP_STATUS:200`.
- Body: `direccion` actualizada, `agente_id` sigue siendo `610141d9-...` (Agente A, quien publicó originalmente) — no cambió a B a pesar de que B fue quien editó.
- **Esperado vs obtenido**: coincide — 200, `agente_id` inmutable.

### 9.5 — Agente C (otra agencia) intenta editar el mismo inmueble

```
curl -X PUT http://localhost:8000/inmuebles/<inmueble_id> \
  -H "Authorization: Bearer <AGENTEC_JWT>" -H "Content-Type: application/json" \
  -d '{"direccion":"Intento no autorizado de Agente C", ... }'
```

- **Resultado**: `HTTP_STATUS:403`, `{"detail":"No autorizado para operar sobre este inmueble"}`.
- **Esperado vs obtenido**: coincide — 403.

### 9.6 — Agente A despublica el inmueble (`PATCH /disponibilidad`)

```
curl -X PATCH http://localhost:8000/inmuebles/<inmueble_id>/disponibilidad \
  -H "Authorization: Bearer <AGENTEA_JWT>" -H "Content-Type: application/json" \
  -d '{"nuevo_estado": "oculto"}'
```

- **Resultado**: `HTTP_STATUS:200`, `estado: "oculto"` en el body.
- **Esperado vs obtenido**: coincide.

### 9.7 — `GET /inmuebles/gestionados`

- Como **Agente A**: `HTTP_STATUS:200`, lista con 1 elemento — el inmueble de María (`estado: "oculto"`, `agente_id` de A).
- Como **Agente C**: `HTTP_STATUS:200`, lista vacía `[]` (no gestiona ningún propietario con relación activa).
- **Esperado vs obtenido**: coincide en ambos casos.

### Casos extra (no bloqueantes, agregados para cubrir huecos evidentes)

- `GET /inmuebles/gestionados` sin token → `HTTP_STATUS:401`, `{"detail":"Missing authentication token"}`.
- `PUT /inmuebles/00000000-0000-0000-0000-000000000000` (inmueble inexistente) con JWT de Agente A → `HTTP_STATUS:404`, `{"detail":"Inmueble 00000000-0000-0000-0000-000000000000 no existe"}`.

## Hallazgos

Ningún bug encontrado. Todos los escenarios de autorización cross-domain (agente con relación activa, agente sin relación, agente de otra agencia, inmutabilidad de `agente_id`, listado por agencia) se comportaron exactamente según lo especificado en `design.md` y `specs/inmuebles/spec.md` de este change.

## Restauración de la Base de Datos y MinIO

1. **MinIO**: se eliminó el objeto subido en 9.2 (`storage_key: inmuebles/1398ec55-.../4ba7afd2-....jpg`, bucket `inmuebles`) vía `boto3` (`S3StorageAdapter._client.delete_object`, ejecutado dentro del contenedor `backend`). Se verificó con `list_objects_v2(Prefix="inmuebles/")` que no queda ningún objeto residual.
2. **Postgres** (`docker compose exec -T postgres psql -U rentame -d rentame`):
   ```sql
   DELETE FROM foto_inmueble WHERE inmueble_id = '<inmueble_id>';
   DELETE FROM inmueble WHERE id = '<inmueble_id>';
   DELETE FROM relacion_agencia_propietario WHERE id = '<relacion_id>';
   DELETE FROM solicitud_ingreso_agencia WHERE id = '<solicitud_id>';
   UPDATE usuario SET agencia_id = NULL WHERE id IN (<A>, <B>, <C>);
   DELETE FROM agencia WHERE id IN (<agencia_AB>, <agencia_C>);
   DELETE FROM usuario WHERE id IN (<Maria>, <A>, <B>, <C>);
   ```
   (No existen endpoints `DELETE` para `usuario`/`agencia`/`relacion`/`solicitud` en el backlog actual — la limpieza de estas entidades de prueba se hizo con SQL directo, igual que su creación.)

## Verificación de Estado de Base de Datos (post-limpieza)

```
inmueble | usuario | agencia | relacion | solicitud | foto
---------+---------+---------+----------+-----------+-----
       0 |       1 |       0 |        0 |         0 |    0
```

Idéntico al baseline pre-test. Estado restaurado: **Sí**.

## Resultado

- Estado del Paso 9: PASS
- Tareas 9.1 a 9.10 marcadas como completadas en `tasks.md`.
- Issues bloqueantes: ninguno.
