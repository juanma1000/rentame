# Reporte Paso 10 - Testing Manual de Endpoints con curl

- Fecha: 2026-09-06
- Cambio: firma-electronica-contrato-arrendamiento
- Agente: qa-expert (Claude Code)

`docker compose ps` confirmó `rentame-backend` up (2 semanas, bind mount + `--reload`, sirve código actual sin rebuild necesario). `docker compose exec backend alembic current` confirmó migración `c3d4e5f6a7b8 (head)` aplicada, con las tablas `contratos` y `arrendamientos_activos` ya presentes (ver reporte del paso 9). Todos los comandos se ejecutaron desde el host contra `http://localhost:8000`, con Postgres real (DB `rentame`). Baseline pre-test: `usuario`=12, `validaciones_identidad`=0, `polizas_arrendamiento`=0, `contratos`=0, `arrendamientos_activos`=0.

Archivos usados como documentos dummy: `/tmp/frente.jpg` y `/tmp/dorso.jpg` (ya existentes de la corrida manual del change anterior, texto plano arbitrario — ni `identidad` ni `seguro_arrendamiento` validan el formato, solo reenvían los bytes al `FakeAdapter`).

## 1. Preparación: cuenta inquilino con identidad verificada y póliza aprobada

```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino.firma@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino Firma","rol":"inquilino"}'
```
→ `usuario.id=b862d69b-a6b1-47ba-b38c-ebbdfcd99f2e` (guardado como `$TOKEN`).

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=5551234567" -F "imagen_frente=@/tmp/frente.jpg" -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `200` — `{"id":"925115e5-91c1-447f-815d-449697f5c509","estado":"aprobado","referencia_externa":"FAKE-3c95277da5fd0da6"}`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/seguro-arrendamiento/contratar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=5551234567" -F "documentos=@/tmp/frente.jpg" -F "documentos=@/tmp/dorso.jpg"
```
→ `200` — `{"id":"08e42fb8-ae03-4e94-98bb-0290cd1b2d4d","estado":"aprobada","prima_mensual":45000.0,"referencia_externa":"FAKE-3c95277da5fd0da6"}`

Esta cuenta ya tiene una `PolizaArrendamiento` en estado `aprobada`, lista para los pasos 2 y 4.

## 2. `POST /firma-contrato/generar` — inquilino CON póliza aprobada (tarea 10.2)

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/generar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"inmueble_id":"11111111-1111-1111-1111-111111111111","nombre_inquilino":"Curl Inquilino Firma","nombre_propietario":"Propietario Curl","direccion_inmueble":"Calle 123 #45-67","canon_mensual":1500000,"duracion_meses":12}'
```
→ `200`
```json
{"id":"34b649a9-2ccb-46ba-bff0-faedd82a46d9","estado":"enviado_a_firma","referencia_externa":"FAKE-e6a28803b6b7799f"}
```
Estado `enviado_a_firma` confirmado, tal como exige la tarea 10.2. Este contrato se usa en el paso 4 (webhook `firmado`).

## 3. `POST /firma-contrato/generar` — inquilino SIN póliza aprobada (tarea 10.3)

Preparación de una segunda cuenta, con identidad verificada pero SIN pasar por `/seguro-arrendamiento/contratar`:
```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino.firma.nopoliza@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino Sin Poliza","rol":"inquilino"}'
```
→ `usuario.id=c53ecc72-87b4-43c9-a832-b5bfed30d9b8` (guardado como `$TOKEN2`).

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $TOKEN2" \
  -F "cedula=5559998888" -F "imagen_frente=@/tmp/frente.jpg" -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `200` — `{"id":"0f3b019a-baea-4144-9a91-12658e656ddc","estado":"aprobado","referencia_externa":"FAKE-d01c3a1a8a8a9c3a"}` (identidad verificada, pero sin póliza de seguro contratada)

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/generar \
  -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" \
  -d '{"inmueble_id":"22222222-2222-2222-2222-222222222222","nombre_inquilino":"Curl Inquilino Sin Poliza","nombre_propietario":"Propietario Curl","direccion_inmueble":"Calle 999","canon_mensual":1200000,"duracion_meses":12}'
```
→ `403`
```json
{"detail":"La cuenta c53ecc72-87b4-43c9-a832-b5bfed30d9b8 no tiene una PolizaArrendamiento aprobada"}
```
(status code mapeado en `main.py` desde `firma_contrato.domain.exceptions.PolizaNoAprobada`, confirmado leyendo `main.py` líneas 187-189, `poliza_no_aprobada_handler` → `JSONResponse(status_code=403, ...)`.)

Verificación de que el rechazo ocurrió antes de generar cualquier documento (no se creó ningún contrato para esta cuenta):
```sql
SELECT count(*) FROM contratos WHERE usuario_id='c53ecc72-87b4-43c9-a832-b5bfed30d9b8';
```
→ `0`, consistente con el test automatizado `test_should_reject_explicitly_when_no_poliza_aprobada`, que gatea contra `poliza_arrendamiento_repository` antes de invocar al `proveedor` de firma.

## 4. `POST /firma-contrato/webhook` — resultado `firmado` (tarea 10.4)

Usando el contrato generado en el paso 2 (`referencia_externa=FAKE-e6a28803b6b7799f`):
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/webhook \
  -H "Content-Type: application/json" \
  -d '{"referencia_externa":"FAKE-e6a28803b6b7799f","estado":"firmado"}'
```
→ `200`
```json
{"id":"34b649a9-2ccb-46ba-bff0-faedd82a46d9","estado":"firmado","referencia_externa":"FAKE-e6a28803b6b7799f"}
```

Verificación directa en la tabla `arrendamientos_activos`:
```sql
SELECT id, usuario_id, contrato_id, estado FROM arrendamientos_activos WHERE contrato_id='34b649a9-2ccb-46ba-bff0-faedd82a46d9';
```
→
```
 id=cc449384-dd58-42f0-bc30-17d5125b432e | usuario_id=b862d69b-a6b1-47ba-b38c-ebbdfcd99f2e | contrato_id=34b649a9-2ccb-46ba-bff0-faedd82a46d9 | estado=activo
```
Confirmado: se creó el `ArrendamientoActivo` a partir del contrato `firmado`, tal como exige la tarea 10.4.

## 5. `POST /firma-contrato/webhook` — resultado `rechazado` (tarea 10.5)

Se generó un segundo contrato distinto sobre la misma cuenta (que sigue con póliza `aprobada`), para no reutilizar el ya `firmado` del paso 4:
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/generar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"inmueble_id":"33333333-3333-3333-3333-333333333333","nombre_inquilino":"Curl Inquilino Firma","nombre_propietario":"Propietario Curl","direccion_inmueble":"Calle 456 #78-90","canon_mensual":1600000,"duracion_meses":12}'
```
→ `200` — `{"id":"ee7b312b-174e-4af5-a15d-b9201e45a618","estado":"enviado_a_firma","referencia_externa":"FAKE-06465d21c91aad4a"}`

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/firma-contrato/webhook \
  -H "Content-Type: application/json" \
  -d '{"referencia_externa":"FAKE-06465d21c91aad4a","estado":"rechazado"}'
```
→ `200`
```json
{"id":"ee7b312b-174e-4af5-a15d-b9201e45a618","estado":"rechazado","referencia_externa":"FAKE-06465d21c91aad4a"}
```

Verificación de que NO se creó `ArrendamientoActivo` para este contrato:
```sql
SELECT count(*) FROM arrendamientos_activos WHERE contrato_id='ee7b312b-174e-4af5-a15d-b9201e45a618';
```
→ `0`

Verificación de que la póliza asociada a la cuenta sigue en estado `aprobada` (no fue tocada por el webhook):
```sql
SELECT id, estado FROM polizas_arrendamiento WHERE usuario_id='b862d69b-a6b1-47ba-b38c-ebbdfcd99f2e';
```
→ `id=08e42fb8-ae03-4e94-98bb-0290cd1b2d4d | estado=aprobada`

Ambas verificaciones confirman lo esperado, consistente con el test automatizado `test_rechazado_does_not_create_arrendamiento_and_poliza_stays_aprobada`.

## Restauración de la base de datos

```sql
DELETE FROM arrendamientos_activos WHERE usuario_id IN (SELECT id FROM usuario WHERE email IN ('curl.inquilino.firma@rentame.test','curl.inquilino.firma.nopoliza@rentame.test'));
DELETE FROM contratos WHERE usuario_id IN (SELECT id FROM usuario WHERE email IN ('curl.inquilino.firma@rentame.test','curl.inquilino.firma.nopoliza@rentame.test'));
DELETE FROM polizas_arrendamiento WHERE usuario_id IN (SELECT id FROM usuario WHERE email IN ('curl.inquilino.firma@rentame.test','curl.inquilino.firma.nopoliza@rentame.test'));
DELETE FROM validaciones_identidad WHERE usuario_id IN (SELECT id FROM usuario WHERE email IN ('curl.inquilino.firma@rentame.test','curl.inquilino.firma.nopoliza@rentame.test'));
DELETE FROM usuario WHERE email IN ('curl.inquilino.firma@rentame.test','curl.inquilino.firma.nopoliza@rentame.test');
```
Conteos post-limpieza (DB `rentame`): `usuario`=12, `validaciones_identidad`=0, `polizas_arrendamiento`=0, `contratos`=0, `arrendamientos_activos`=0 — idénticos al baseline pre-test.

## Resultado
- Estado del Paso 10: PASS
- Issues bloqueantes: ninguno.
