# Reporte Paso 6 - Testing Manual de Endpoints con curl

- Fecha: 2026-09-06
- Cambio: frontend-flujo-arrendamiento
- Alcance: sección 6 de `tasks.md`
- Agente: qa-expert (Claude Code)

`docker compose ps` confirmó los 5 servicios up, `rentame-backend` con bind mount (`/home/juanma100/code/Rentame/backend` → `/app`, confirmado con `docker inspect`) y `--reload`, sirviendo el código actual de este change sin necesidad de rebuild. Todos los comandos se ejecutaron desde el host contra `http://localhost:8000`, con Postgres real (DB `rentame`). Baseline pre-test (verificado antes de empezar): `validaciones_identidad`=0, `polizas_arrendamiento`=0, `contratos`=0, `arrendamientos_activos`=0, `pagos`=0.

Confirmación previa de que los 3 endpoints nuevos ya están montados y protegidos por JWT:
```
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/identidad/estado
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/seguro-arrendamiento/estado
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/firma-contrato/estado
```
→ `401` en los tres, sin `Authorization`.

## 1. Preparación: propietario + inquilino

```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.propietario.frontend2@rentame.test","password":"Secreta123!","nombre":"Curl Propietario Frontend2","rol":"propietario"}'
```
→ `propietario.id=335a803e-de47-47ff-9b3d-26f2c71ec5ce` (guardado como `$PROP_TOKEN`).

```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino.frontend2@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino Frontend2","rol":"inquilino"}'
```
→ `inquilino.id=bbd123a4-b73d-4271-a8db-cbc51a517006` (guardado como `$INQ_TOKEN`).

Nota: un primer intento de registro (emails `curl.propietario.frontend@rentame.test` / `curl.inquilino.frontend@rentame.test`, sin sufijo `2`) falló solo en la extracción local del token por un error de script (se buscó la clave `token` en vez de `access_token` en la respuesta JSON) — los usuarios sí quedaron creados en la DB pero nunca se usaron para ninguna llamada autenticada. Se limpiaron junto con el resto de los datos de prueba (ver sección de restauración).

## 2. Tarea 6.3 — `GET /identidad/estado` antes y después de validar

Antes:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/identidad/estado -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200` — `{"estado":"no_iniciado"}`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $INQ_TOKEN" \
  -F "cedula=7001112244" -F "imagen_frente=@/tmp/frente.jpg" -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `200` — `{"id":"4dd4d888-5f90-4309-9b80-a9b708dffa85","estado":"aprobado","referencia_externa":"FAKE-17d8abdc15f7eb8c"}` (`FakeAdapter` aprueba siempre)

Después:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/identidad/estado -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200` — `{"estado":"aprobado"}` — confirma la tarea 6.3.

## 3. Tarea 6.4 — `GET /seguro-arrendamiento/estado` antes y después de contratar

Antes (ver también sección 4 más abajo, capturado en el mismo batch inicial):
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/seguro-arrendamiento/estado -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200` — `{"estado":"no_iniciado","prima_mensual":null}`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/seguro-arrendamiento/contratar \
  -H "Authorization: Bearer $INQ_TOKEN" \
  -F "cedula=7001112244" -F "documentos=@/tmp/frente.jpg" -F "documentos=@/tmp/dorso.jpg"
```
→ `200` — `{"id":"34064902-785d-4148-a622-b48a5fecc7cb","estado":"aprobada","prima_mensual":45000.0,"referencia_externa":"FAKE-17d8abdc15f7eb8c"}`

Después:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/seguro-arrendamiento/estado -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200` — `{"estado":"aprobada","prima_mensual":45000.0}` — confirma la tarea 6.4 (`aprobada` + `prima_mensual` presente).

## 4. Tarea 6.5 — `GET /firma-contrato/estado` antes, en `enviado_a_firma`, y después de firmado

Antes (capturado antes de generar el contrato):
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/firma-contrato/estado -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200` — `{"estado":"no_iniciado","arrendamiento_activo_id":null}`

Se creó un `Inmueble` real (necesario porque `firma-contrato/generar` valida `inmueble_id`):
```
curl -X POST http://localhost:8000/inmuebles/ -H "Authorization: Bearer $PROP_TOKEN" \
  -F "direccion=Calle Frontend 200" -F "barrio=Centro" -F "ciudad=Bogota" -F "tipo=apartamento" \
  -F "area_m2=55" -F "habitaciones=2" -F "banos=1" -F "valor_mensual=1200000" \
  -F "descripcion=Inmueble de prueba para curl frontend-flujo-arrendamiento" -F "fotos=@/tmp/foto1.jpg"
```
→ `201` — `inmueble.id=60b6bcbd-a011-4126-baa3-180b85cee315`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/generar \
  -H "Authorization: Bearer $INQ_TOKEN" -H "Content-Type: application/json" \
  -d '{"inmueble_id":"60b6bcbd-a011-4126-baa3-180b85cee315","nombre_inquilino":"Curl Inquilino Frontend2","nombre_propietario":"Curl Propietario Frontend2","direccion_inmueble":"Calle Frontend 200","canon_mensual":1200000,"duracion_meses":12}'
```
→ `200` — `{"id":"d2afc7da-e439-4229-a916-0c855f9dde27","estado":"enviado_a_firma","referencia_externa":"FAKE-ea4c40459c22ea7b"}`

Estado intermedio (`enviado_a_firma`, sin `arrendamiento_activo_id` todavía):
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/firma-contrato/estado -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200` — `{"estado":"enviado_a_firma","arrendamiento_activo_id":null}`

Webhook simulado con resultado `firmado`:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/webhook \
  -H "Content-Type: application/json" \
  -d '{"referencia_externa":"FAKE-ea4c40459c22ea7b","estado":"firmado"}'
```
→ `200` — `{"id":"d2afc7da-e439-4229-a916-0c855f9dde27","estado":"firmado","referencia_externa":"FAKE-ea4c40459c22ea7b"}`

Después:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X GET http://localhost:8000/firma-contrato/estado -H "Authorization: Bearer $INQ_TOKEN"
```
→ `200` — `{"estado":"firmado","arrendamiento_activo_id":"d50e987b-f0ef-4e6d-b8f6-a83654ff6585"}` — confirma la tarea 6.5 (`firmado` + `arrendamiento_activo_id` presente).

Verificación directa en base de datos (tarea 6.2, confirmando la creación real del `ArrendamientoActivo` al final de la cadena):
```sql
SELECT id, usuario_id, contrato_id, inmueble_id, estado FROM arrendamientos_activos WHERE id='d50e987b-f0ef-4e6d-b8f6-a83654ff6585';
```
→ `id=d50e987b-f0ef-4e6d-b8f6-a83654ff6585 | usuario_id=bbd123a4-b73d-4271-a8db-cbc51a517006 | contrato_id=d2afc7da-e439-4229-a916-0c855f9dde27 | inmueble_id=60b6bcbd-a011-4126-baa3-180b85cee315 | estado=activo`

## Resumen de la cadena completa (tarea 6.2)

`registro inquilino` → `registro propietario` → `POST /identidad/validar` (aprobado por `FakeAdapter`) → `POST /seguro-arrendamiento/contratar` (aprobada por `FakeAdapter`, `prima_mensual=45000.0`) → `POST /inmuebles/` (inmueble real requerido por `firma_contrato`) → `POST /firma-contrato/generar` (`enviado_a_firma`) → `POST /firma-contrato/webhook` con `estado=firmado` → `ArrendamientoActivo` creado (`estado=activo`). Cada uno de los 3 `GET /estado` fue verificado antes y después del paso correspondiente, con las tres transiciones esperadas: `no_iniciado → aprobado`, `no_iniciado → aprobada` (con `prima_mensual`), `no_iniciado → enviado_a_firma → firmado` (con `arrendamiento_activo_id`).

## Restauración de la base de datos

```sql
DELETE FROM arrendamientos_activos WHERE id='d50e987b-f0ef-4e6d-b8f6-a83654ff6585';
DELETE FROM contratos WHERE id='d2afc7da-e439-4229-a916-0c855f9dde27';
DELETE FROM foto_inmueble WHERE inmueble_id='60b6bcbd-a011-4126-baa3-180b85cee315';
DELETE FROM inmueble WHERE id='60b6bcbd-a011-4126-baa3-180b85cee315';
DELETE FROM polizas_arrendamiento WHERE usuario_id IN (SELECT id FROM usuario WHERE email LIKE '%frontend%');
DELETE FROM validaciones_identidad WHERE usuario_id IN (SELECT id FROM usuario WHERE email LIKE '%frontend%');
DELETE FROM usuario WHERE email LIKE '%frontend%';
```
Este `DELETE` por patrón `LIKE '%frontend%'` también eliminó los 2 usuarios sobrantes del intento fallido de extracción de token de la sección 1 (nunca fueron usados para ninguna llamada de negocio, solo quedaron registrados sin datos asociados).

Conteos post-limpieza (DB `rentame`): `validaciones_identidad`=0, `polizas_arrendamiento`=0, `contratos`=0, `arrendamientos_activos`=0, `pagos`=0, usuarios con email `%frontend%`=0 — idénticos al baseline pre-test.

Nota: el objeto de la foto subida a MinIO (bucket `inmuebles`, key `inmuebles/17686dd7-.../b5f616e8-....jpg`) no fue borrado del bucket — la fila de `foto_inmueble` que lo referenciaba en Postgres sí fue eliminada arriba. Inofensivo: es un objeto huérfano en un bucket de desarrollo local (MinIO), sin ninguna fila en la base de datos que lo referencie ni ningún proceso que lo liste por convención de nombre (mismo patrón ya documentado en el reporte de curl del change `pago-mensual-renta`).

## Resultado
- Estado del Paso 6 (sección 6 de `tasks.md`): PASS — la cadena completa identidad → seguro → firma-contrato → arrendamiento activo se ejerció con éxito end-to-end vía curl, y los 3 endpoints `GET /estado` nuevos devolvieron la forma y los valores esperados en cada punto de la cadena.
- Issues bloqueantes: ninguno.
