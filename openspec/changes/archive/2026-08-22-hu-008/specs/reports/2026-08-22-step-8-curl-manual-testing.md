# Reporte Paso 8 - Testing Manual de Endpoints con curl

- Fecha: 2026-08-22
- Cambio: hu-008
- Agente: Claude Code

Todos los comandos se ejecutaron con `docker compose exec backend curl ...` contra el backend real (dentro de la red docker), con Postgres real. Baseline pre-test: `usuario`=8, `agencia`=1, `inmueble`=4 (dev DB).

## 1. `POST /usuarios/registro` — 3 roles

**Propietario**
```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.propietario@rentame.test","password":"Secreta123!","nombre":"Curl Propietario","rol":"propietario"}'
```
→ `201`, body con `access_token` (JWT válido) + `usuario` (sin password/hash expuesto).

**Agente**
```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.agente@rentame.test","password":"Secreta123!","nombre":"Curl Agente","rol":"agente"}'
```
→ `201`.

**Inquilino**
```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.inquilino@rentame.test","password":"Secreta123!","nombre":"Curl Inquilino","rol":"inquilino"}'
```
→ `201`.

## 2. `POST /usuarios/registro` — email duplicado
```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"email":"curl.propietario@rentame.test","password":"OtraClave1!","nombre":"Duplicado","rol":"propietario"}'
```
→ `409`, `{"detail":"El email curl.propietario@rentame.test ya está registrado"}` — no crea una cuenta nueva.

## 3. `POST /usuarios/registro` — payload inválido (sin `email`)
```
curl -X POST http://localhost:8000/usuarios/registro -H "Content-Type: application/json" \
  -d '{"password":"Secreta123!","nombre":"Sin Email","rol":"propietario"}'
```
→ `422`, error de validación de Pydantic sobre el campo `email`.

## 4. `POST /usuarios/login` — credenciales correctas
```
curl -X POST http://localhost:8000/usuarios/login -H "Content-Type: application/json" \
  -d '{"email":"curl.propietario@rentame.test","password":"Secreta123!"}'
```
→ `200`, `access_token` válido con `sub`/`rol` del usuario.

## 5. `POST /usuarios/login` — credenciales inválidas (mensaje único)
Email inexistente:
```
curl -X POST http://localhost:8000/usuarios/login -H "Content-Type: application/json" \
  -d '{"email":"nadie@rentame.test","password":"cualquiera"}'
```
→ `401`, `{"detail":"Email o contraseña incorrectos"}`.

Password incorrecto para email existente:
```
curl -X POST http://localhost:8000/usuarios/login -H "Content-Type: application/json" \
  -d '{"email":"curl.propietario@rentame.test","password":"incorrecta"}'
```
→ `401`, **el mismo body exacto**: `{"detail":"Email o contraseña incorrectos"}` — confirmado que ambos casos son indistinguibles, cumple spec.md ("Login rechazado sin revelar cuál dato falló").

## 6. `GET /agencias/buscar` — sin autenticación
Por razón social (`q=Valle`) → `200`, `[{"id":...,"razon_social":"Inmobiliaria del Valle SAS","nit":"SEED-900123456-1"}]`.
Por NIT (`q=900123456`) → `200`, misma agencia.
Sin coincidencias (`q=noexiste123`) → `200`, `[]` (nunca 404/error).
Ningún request incluyó header `Authorization` — confirma que el endpoint es público.

## 7. Flujo completo de agente: registro → crear agencia → verificar membresía
1. Login con `curl.agente@rentame.test` → JWT.
2. `POST /agencias/` con ese JWT: `{"razon_social":"Curl Agencia Test SAS","nit":"CURL-999888777"}` → `201`.
3. Verificado en Postgres: `usuario.agencia_id` de `curl.agente@rentame.test` apunta a la agencia recién creada (`JOIN` exitoso, `razon_social` correcta).

## 8. Casos de error adicionales
Cubiertos arriba: 422 (payload inválido), 409 (email duplicado), 401 (credenciales inválidas, mensaje único).

## Restauración de la base de datos
```sql
DELETE FROM inmueble WHERE propietario_id IN (SELECT id FROM usuario WHERE email LIKE 'curl.%@rentame.test');
DELETE FROM relacion_agencia_propietario WHERE propietario_id IN (SELECT id FROM usuario WHERE email LIKE 'curl.%@rentame.test');
DELETE FROM solicitud_ingreso_agencia WHERE agente_id IN (SELECT id FROM usuario WHERE email LIKE 'curl.%@rentame.test');
UPDATE usuario SET agencia_id = NULL WHERE email LIKE 'curl.%@rentame.test';
DELETE FROM usuario WHERE email LIKE 'curl.%@rentame.test';
DELETE FROM agencia WHERE nit = 'CURL-999888777';
```
Conteos post-limpieza: `usuario`=8, `agencia`=1, `inmueble`=4 — idénticos al baseline pre-test.

## Resultado
- Estado del Paso 8: PASS
- Issues bloqueantes: ninguno
