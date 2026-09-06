# Reporte Paso 9 - Testing Manual de Endpoints con curl

- Fecha: 2026-09-06
- Cambio: validacion-identidad-inquilino
- Agente: qa-expert (Claude Code)

`docker compose up` ya estaba corriendo (`rentame-backend` up hace 2 semanas, montado con bind mount + `--reload`, por lo que sirve el código actual sin rebuild). Se confirmó con `docker compose exec backend alembic current` que la migración `a1b2c3d4e5f6 (head)` ("create validaciones_identidad table, add identidad_verificada to usuario") ya estaba aplicada tanto en `rentame` (dev) como en `rentame_test`. Todos los comandos se ejecutaron desde el host contra `http://localhost:8000`, con Postgres real. Baseline pre-test (DB `rentame`): `usuario`=12, `validaciones_identidad`=0.

## 0. Preparación: cuenta inquilino de prueba

```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino.identidad@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino Identidad","rol":"inquilino"}'
```
→ `201` (implícito, `AuthResponse`), body:
```json
{"access_token":"eyJhbGci...","usuario":{"id":"a08a5a37-3c03-4d0f-b3e1-85a0493ca9a2","email":"curl.inquilino.identidad@rentame.test","nombre":"Curl Inquilino Identidad","rol":"inquilino"}}
```
`access_token` guardado para los requests siguientes (`Authorization: Bearer <token>`).

Archivos usados como imágenes dummy: `/tmp/frente.jpg` y `/tmp/dorso.jpg` (contenido de texto plano arbitrario — el endpoint no valida el formato de imagen, solo reenvía los bytes al `FakeAdapter`, que siempre aprueba).

## 1. `POST /identidad/validar` — payload válido, primera vez

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=1234567890" \
  -F "imagen_frente=@/tmp/frente.jpg" \
  -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `200`
```json
{"id":"1fff97a4-5c26-41e3-b6f8-8bcaeb15efd9","estado":"aprobado","referencia_externa":"FAKE-c775e7b757ede630"}
```

Verificación en Postgres (no hay endpoint GET de perfil de usuario en este proyecto, por lo que la verificación de `identidad_verificada` se hizo directo contra la tabla `usuario`):
```sql
SELECT id, email, identidad_verificada FROM usuario WHERE email='curl.inquilino.identidad@rentame.test';
```
→ `identidad_verificada = t` (True).

```sql
SELECT id, usuario_id, cedula, estado, referencia_externa FROM validaciones_identidad WHERE usuario_id=(SELECT id FROM usuario WHERE email='curl.inquilino.identidad@rentame.test');
```
→ una única fila: `cedula=1234567890, estado=aprobado, referencia_externa=FAKE-c775e7b757ede630`. Solo cédula/estado/fecha/referencia quedaron persistidos — ningún byte de imagen aparece en ninguna columna ni tabla, consistente con el test automatizado `test_image_bytes_never_reach_the_database` (sección 5.2).

## 2. `POST /identidad/validar` — segundo intento sobre la misma cuenta ya verificada

```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=1234567890" \
  -F "imagen_frente=@/tmp/frente.jpg" \
  -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `409`
```json
{"detail":"La cuenta a08a5a37-3c03-4d0f-b3e1-85a0493ca9a2 ya tiene una validación de identidad aprobada"}
```
(status code mapeado en `main.py` desde `identidad.domain.exceptions.IdentidadYaVerificada`, confirmado leyendo `main.py` antes de asumir el código — el agente previo implementó el gate en `usuario_repository.esta_verificado` antes de llamar al `proveedor`).

Verificación de que no se llamó al proveedor una segunda vez (no se creó una segunda fila):
```sql
SELECT count(*) FROM validaciones_identidad WHERE usuario_id=(SELECT id FROM usuario WHERE email='curl.inquilino.identidad@rentame.test');
```
→ `1` (sin cambio respecto al paso anterior).

## 3. `POST /identidad/validar` — payload inválido

**Sin `cedula`:**
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $TOKEN" \
  -F "imagen_frente=@/tmp/frente.jpg" \
  -F "imagen_dorso=@/tmp/dorso.jpg"
```
→ `422`
```json
{"detail":[{"type":"missing","loc":["body","cedula"],"msg":"Field required","input":null}]}
```

**Sin imágenes:**
```
curl -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/identidad/validar \
  -H "Authorization: Bearer $TOKEN" \
  -F "cedula=1234567890"
```
→ `422`
```json
{"detail":[{"type":"missing","loc":["body","imagen_frente"],"msg":"Field required","input":null},{"type":"missing","loc":["body","imagen_dorso"],"msg":"Field required","input":null}]}
```

## Restauración de la base de datos

```sql
DELETE FROM validaciones_identidad WHERE usuario_id=(SELECT id FROM usuario WHERE email='curl.inquilino.identidad@rentame.test');
DELETE FROM usuario WHERE email='curl.inquilino.identidad@rentame.test';
```
Conteos post-limpieza (DB `rentame`): `usuario`=12, `validaciones_identidad`=0 — idénticos al baseline pre-test.

## Resultado
- Estado del Paso 9: PASS
- Issues bloqueantes: ninguno.
