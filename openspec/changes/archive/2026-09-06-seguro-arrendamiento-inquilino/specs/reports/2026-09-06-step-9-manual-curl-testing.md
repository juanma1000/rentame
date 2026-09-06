# Reporte Paso 9 - Testing Manual de Endpoints con curl

- Fecha: 2026-09-06
- Cambio: seguro-arrendamiento-inquilino
- Agente: qa-expert (Claude Code)

`docker compose up` ya estaba corriendo (`rentame-backend` up hace 2 semanas, montado con bind mount + `--reload`, por lo que sirve el código actual sin rebuild). Se confirmó con `docker compose exec backend alembic current` que la migración `b2c3d4e5f6a7 (head)` (tabla `polizas_arrendamiento`) ya estaba aplicada tanto en `rentame` (dev) como en `rentame_test` (ver reporte del paso 8). Todos los comandos se ejecutaron desde el host contra `http://localhost:8000`, con Postgres real. Baseline pre-test (DB `rentame`): `usuario`=12, `validaciones_identidad`=0, `polizas_arrendamiento`=0.

Archivos usados como documentos dummy: `/tmp/frente.jpg` y `/tmp/dorso.jpg` (texto plano arbitrario — el endpoint no valida el formato, solo reenvía los bytes al `FakeAdapter`, que siempre aprueba, y no los persiste).

## 0. Preparación: cuenta inquilino con identidad ya verificada

```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino.seguro@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino Seguro","rol":"inquilino"}'
```
→ body con `access_token` y `usuario.id=24ed0113-7737-4535-ab41-ef9f32b4f401` (guardado como `$TOKEN`).

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=9876543210" \
  -F "imagen_frente=@/tmp/frente.jpg" \
  -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `200`
```json
{"id":"ca26ac33-b8d6-4e64-9f36-5d908b1fe6c6","estado":"aprobado","referencia_externa":"FAKE-7619ee8cea49187f"}
```
Esta cuenta queda con `usuario.identidad_verificada = true` para los pasos siguientes.

## 1. `POST /seguro-arrendamiento/contratar` — payload válido, cuenta con identidad verificada

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/seguro-arrendamiento/contratar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=9876543210" \
  -F "documentos=@/tmp/frente.jpg" \
  -F "documentos=@/tmp/dorso.jpg"
```
→ `200`
```json
{"id":"eeff0ab2-f781-4f2f-a1af-bf0e7fd0bd7d","estado":"aprobada","prima_mensual":45000.0,"referencia_externa":"FAKE-7619ee8cea49187f"}
```
Estado `aprobada` con `prima_mensual` presente, tal como exige la tarea 9.2. `referencia_externa` es determinística para la misma cédula (`FakeAdapter`), consistente con el test automatizado `test_contratar_returns_deterministic_result_for_same_cedula`.

## 2. `POST /seguro-arrendamiento/contratar` — cuenta SIN identidad verificada

Preparación de una segunda cuenta, sin pasar por `/identidad/validar`:
```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino.seguro.noverif@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino No Verificado","rol":"inquilino"}'
```
→ `usuario.id=5c6e6bc4-913d-40fc-999f-6de815189090` (guardado como `$TOKEN2`).

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/seguro-arrendamiento/contratar \
  -H "Authorization: Bearer $TOKEN2" \
  -F "cedula=1111111111" \
  -F "documentos=@/tmp/frente.jpg" \
  -F "documentos=@/tmp/dorso.jpg"
```
→ `403`
```json
{"detail":"La cuenta 5c6e6bc4-913d-40fc-999f-6de815189090 no tiene la identidad verificada"}
```
(status code mapeado en `main.py` desde `seguro_arrendamiento.domain.exceptions.IdentidadNoVerificada`, confirmado leyendo `main.py` — línea 160-164, `identidad_no_verificada_handler` → `JSONResponse(status_code=403, ...)` — antes de asumir el código.)

Verificación de que el rechazo ocurrió antes de llamar al proveedor de seguro (no se creó ninguna póliza para esta cuenta):
```sql
SELECT count(*) FROM polizas_arrendamiento WHERE usuario_id='5c6e6bc4-913d-40fc-999f-6de815189090';
```
→ `0`, consistente con el test automatizado `test_should_reject_explicitly_when_identidad_not_verificada`, que gatea contra `usuario_identidad_repository.esta_verificado` antes de invocar `proveedor`.

## 3. `POST /seguro-arrendamiento/contratar` — payload inválido (sin `documentos`)

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/seguro-arrendamiento/contratar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=9876543210"
```
→ `422`
```json
{"detail":[{"type":"missing","loc":["body","documentos"],"msg":"Field required","input":null}]}
```

## Restauración de la base de datos

```sql
DELETE FROM polizas_arrendamiento WHERE usuario_id=(SELECT id FROM usuario WHERE email='curl.inquilino.seguro@rentame.test');
DELETE FROM validaciones_identidad WHERE usuario_id=(SELECT id FROM usuario WHERE email='curl.inquilino.seguro@rentame.test');
DELETE FROM usuario WHERE email IN ('curl.inquilino.seguro@rentame.test','curl.inquilino.seguro.noverif@rentame.test');
```
Conteos post-limpieza (DB `rentame`): `usuario`=12, `validaciones_identidad`=0, `polizas_arrendamiento`=0 — idénticos al baseline pre-test.

## Resultado
- Estado del Paso 9: PASS
- Issues bloqueantes: ninguno.
