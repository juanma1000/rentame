# Reporte Paso 10 — Testing Manual de Endpoints con curl (HU-007 gestión de agencias)

- Fecha: 2026-08-21
- Cambio: hu-007
- Agente: Claude (backend-expert), ejecución directa vía Bash contra el backend dockerizado

## Entorno

- Backend: contenedor `rentame-backend` (`http://localhost:8000`), ya corriendo con `--reload`, sin reinicio necesario.
- `curl http://localhost:8000/health` → `200`.
- Base de datos: `rentame-postgres`, base `rentame`, usuario `rentame` (`docker compose exec postgres psql -U rentame -d rentame`).
- JWTs emitidos con `shared.infrastructure.auth.jwt_handler.create_access_token`, ejecutado dentro del contenedor backend:
  `docker compose exec backend python -c "from shared.infrastructure.auth.jwt_handler import create_access_token; print(create_access_token('<uuid>', '<rol>'))"`

## Baseline de base de datos (pre-test)

| tabla | conteo |
|---|---|
| `agencia` | 0 |
| `solicitud_ingreso_agencia` | 0 |
| `relacion_agencia_propietario` | 0 |
| `usuario` | 1 (`demo-owner@test.com`, propietario, preexistente de HU-001 — no tocado) |
| `inmueble` | 0 |

## Usuarios de prueba creados (insertados directo en `usuario` vía psql)

| nombre | id | rol | email |
|---|---|---|---|
| Agente A | `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` | agente | agente-a-hu007@test.com |
| Agente B | `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb` | agente | agente-b-hu007@test.com |
| Agente C | `cccccccc-cccc-cccc-cccc-cccccccccccc` | agente | agente-c-hu007@test.com |
| María (propietaria) | `dddddddd-dddd-dddd-dddd-dddddddddddd` | propietario | maria-hu007@test.com |

Un JWT válido (`exp` ~30 días) fue emitido para cada uno con el helper de la aplicación (no se fabricaron tokens a mano).

## Nota sobre el orden de ejecución (reordenamiento intencional 10.5/10.6)

Siguiendo la instrucción explícita del usuario, el escenario de despublicación en cascada se reordenó para poder probar el **auto-revoke real** (10.6) en vez de dejarlo redundante tras un revoke manual (10.5). Orden ejecutado:

1. 10.2, 10.3, 10.4 (como en `tasks.md`).
2. Insertar inmueble1 (`agente_id` = Agente A, estado `disponible`).
3. Crear Agencia C (único miembro: Agente C).
4. María inicia relación con Agencia C **sin revocar manualmente** la relación con Agencia A.
5. Agente C confirma → se verifica el **auto-revoke** de la relación A-María y la despublicación en cascada de inmueble1 (10.6).
6. Insertar inmueble2 (`agente_id` = Agente C, estado `disponible`).
7. Agente C intenta `/agencias/salir` con la relación C-María aún activa → 409 (primera mitad de 10.7).
8. María revoca **manualmente** la relación C-María → se verifica la despublicación en cascada de inmueble2 (cubre el caso de revoke manual pedido en 10.5, usando la segunda relación en vez de la primera, ya revocada automáticamente en el paso 5).
9. Agente C reintenta `/agencias/salir` (ya sin relaciones activas) → éxito (segunda mitad de 10.7).

Esto prueba ambos caminos de la cascada de despublicación (manual y automática) sin dejar ningún caso sin cubrir.

---

## 10.2 — Crear agencia (Agente A) y rechazo de duplicado

**a) Agente A crea agencia**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/agencias/ \
  -H "Authorization: Bearer <AGENTE_A_JWT>" -H "Content-Type: application/json" \
  -d '{"razon_social":"Agencia Sol S.A.S","nit":"900123456-1"}'
```

Respuesta:
```json
{"id":"f51c2aaf-9fdc-42a3-8845-0481d4337afd","razon_social":"Agencia Sol S.A.S","nit":"900123456-1"}
```
`HTTP_STATUS: 201`

**b) Agente A intenta crear otra agencia → rechazo**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/agencias/ \
  -H "Authorization: Bearer <AGENTE_A_JWT>" -H "Content-Type: application/json" \
  -d '{"razon_social":"Agencia Otra","nit":"900999999-1"}'
```

Respuesta:
```json
{"detail":"El agente aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa ya pertenece a una agencia"}
```
`HTTP_STATUS: 409` — `AgenteYaTieneAgencia` mapeado correctamente.

Verificación en DB: `usuario.agencia_id` de Agente A = `f51c2aaf-9fdc-42a3-8845-0481d4337afd`. ✅

**Resultado: PASS**

---

## 10.3 — Solicitud de ingreso (Agente B) y aprobación (Agente A)

**a) Agente B solicita ingreso**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://localhost:8000/agencias/f51c2aaf-9fdc-42a3-8845-0481d4337afd/solicitudes" \
  -H "Authorization: Bearer <AGENTE_B_JWT>"
```

Respuesta:
```json
{"id":"59a6edba-498a-496e-a0ba-c030e6a4166c","agencia_id":"f51c2aaf-9fdc-42a3-8845-0481d4337afd","agente_id":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","estado":"pendiente"}
```
`HTTP_STATUS: 201`

**b) Agente A aprueba**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://localhost:8000/agencias/solicitudes/59a6edba-498a-496e-a0ba-c030e6a4166c/aprobar" \
  -H "Authorization: Bearer <AGENTE_A_JWT>"
```

Respuesta:
```json
{"id":"59a6edba-498a-496e-a0ba-c030e6a4166c","agencia_id":"f51c2aaf-9fdc-42a3-8845-0481d4337afd","agente_id":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","estado":"aprobada"}
```
`HTTP_STATUS: 200`

Verificación en DB: `usuario.agencia_id` de Agente B = `f51c2aaf-9fdc-42a3-8845-0481d4337afd`. ✅

**Resultado: PASS**

---

## 10.4 — Relación propietario-agencia: inicio (María) y confirmación (Agente A)

**a) María inicia relación con Agencia A**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://localhost:8000/agencias/f51c2aaf-9fdc-42a3-8845-0481d4337afd/relaciones" \
  -H "Authorization: Bearer <MARIA_JWT>"
```

Respuesta:
```json
{"id":"7baf2c70-6a7f-4112-84d9-51505aac03be","agencia_id":"f51c2aaf-9fdc-42a3-8845-0481d4337afd","propietario_id":"dddddddd-dddd-dddd-dddd-dddddddddddd","estado":"pendiente","agente_responsable_id":null}
```
`HTTP_STATUS: 201`

**b) Agente A confirma**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://localhost:8000/agencias/relaciones/7baf2c70-6a7f-4112-84d9-51505aac03be/confirmar" \
  -H "Authorization: Bearer <AGENTE_A_JWT>"
```

Respuesta:
```json
{"id":"7baf2c70-6a7f-4112-84d9-51505aac03be","agencia_id":"f51c2aaf-9fdc-42a3-8845-0481d4337afd","propietario_id":"dddddddd-dddd-dddd-dddd-dddddddddddd","estado":"activa","agente_responsable_id":null}
```
`HTTP_STATUS: 200`

**Resultado: PASS.** Nota (no bloqueante): `confirmar_relacion` no asigna `agente_responsable_id` automáticamente al agente que confirma — queda `null` hasta que se use `PATCH .../responsable` explícitamente. Es consistente con el diseño (`reasignar_responsable` es un caso de uso separado), pero vale la pena confirmarlo con producto: ¿el agente que confirma debería quedar como responsable por defecto? No es un bug de HU-007 (no hay tarea que exija asignación automática), se documenta como observación de diseño.

---

## Preparación del inmueble 1 (directo en DB, HU-002 aún no expone `agente_id` vía API)

```sql
INSERT INTO inmueble (id, propietario_id, agente_id, direccion, barrio, ciudad, tipo, area_m2,
  habitaciones, banos, valor_mensual, descripcion, estado, creado_en, actualizado_en)
VALUES ('e1111111-1111-1111-1111-111111111111', 'dddddddd-dddd-dddd-dddd-dddddddddddd',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Calle 10 # 20-30', 'El Poblado', 'Medellin',
  'apartamento', 65.0, 2, 1, 1200000, 'Apto de prueba HU-007 - gestionado por Agente A',
  'disponible', now(), now());
```
`INSERT 0 1`, verificado con estado `disponible` y `agente_id` = Agente A.

---

## 10.6 — Segunda agencia y auto-revoke real (ejecutado antes del revoke manual, ver nota de reordenamiento)

**a) Crear Agencia C (Agente C, único miembro)**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/agencias/ \
  -H "Authorization: Bearer <AGENTE_C_JWT>" -H "Content-Type: application/json" \
  -d '{"razon_social":"Agencia Luna Ltda","nit":"900555555-1"}'
```
Respuesta: `{"id":"8f9e7b1c-2695-4d55-a0ac-727df5c94c79","razon_social":"Agencia Luna Ltda","nit":"900555555-1"}` — `201`

**b) María inicia relación con Agencia C (SIN revocar antes la de Agencia A)**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://localhost:8000/agencias/8f9e7b1c-2695-4d55-a0ac-727df5c94c79/relaciones" \
  -H "Authorization: Bearer <MARIA_JWT>"
```
Respuesta: `{"id":"564e832d-d9e9-4477-9b69-3a56749597a8", ..., "estado":"pendiente", ...}` — `201`

**c) Agente C confirma → debe disparar auto-revoke + cascada**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://localhost:8000/agencias/relaciones/564e832d-d9e9-4477-9b69-3a56749597a8/confirmar" \
  -H "Authorization: Bearer <AGENTE_C_JWT>"
```
Respuesta: `{"id":"564e832d-...","estado":"activa", ...}` — `200`

**Verificación del auto-revoke y de la cascada:**

```
curl -s -X GET http://localhost:8000/agencias/mia/propietarios -H "Authorization: Bearer <AGENTE_A_JWT>"
```
→ `[{"id":"7baf2c70-...","estado":"revocada", ...}]` — la relación A-María quedó `revocada` **automáticamente**, sin acción manual.

```
curl -s -X GET http://localhost:8000/inmuebles/mios -H "Authorization: Bearer <MARIA_JWT>"
```
→ inmueble1 (`agente_id`=Agente A) con `"estado":"oculto"`.

Confirmado también contra la DB: `relacion_agencia_propietario` muestra `7baf2c70... = revocada`, `564e832d... = activa`; `inmueble.estado` de `e1111111...` = `oculto`.

**Resultado: PASS.** El auto-revoke de `confirmar_relacion` y la cascada de despublicación (`_cascada_despublicacion.py`) funcionan correctamente end-to-end contra Postgres real.

---

## 10.7 (parte 1) — Único agente con relación activa no puede salir

Preparación: inmueble2 insertado directo en DB con `agente_id`=Agente C, `propietario_id`=María, `estado`='disponible' (mismo patrón SQL que inmueble1).

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/agencias/salir \
  -H "Authorization: Bearer <AGENTE_C_JWT>"
```
Respuesta:
```json
{"detail":"El agente cccccccc-cccc-cccc-cccc-cccccccccccc es el último miembro de la agencia 8f9e7b1c-2695-4d55-a0ac-727df5c94c79, que tiene relaciones activas"}
```
`HTTP_STATUS: 409` — `UltimoAgenteConRelacionesActivas` mapeado correctamente.

---

## 10.5 — Revoke manual y verificación de despublicación en cascada

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://localhost:8000/agencias/relaciones/564e832d-d9e9-4477-9b69-3a56749597a8/revocar" \
  -H "Authorization: Bearer <MARIA_JWT>"
```
Respuesta: `{"id":"564e832d-...","estado":"revocada", ...}` — `200`

```
curl -s -X GET http://localhost:8000/inmuebles/mios -H "Authorization: Bearer <MARIA_JWT>"
```
Respuesta (fragmento):
```json
[
  {"id":"e1111111-...","estado":"oculto", ...},
  {"id":"e2222222-...","estado":"oculto", ...}
]
```

Ambos inmuebles (`e1111111...` de Agente A, y `e2222222...` de Agente C) quedaron en `oculto`: el segundo por la cascada disparada por este revoke manual, el primero porque ya había sido despublicado en el paso 10.6.

**Resultado: PASS.** El revoke manual (`revocar_relacion`) dispara correctamente la cascada de despublicación sobre los inmuebles gestionados por agentes de la agencia revocada.

---

## 10.7 (parte 2) — Reintento de salida exitoso tras revocar la relación

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST http://localhost:8000/agencias/salir \
  -H "Authorization: Bearer <AGENTE_C_JWT>"
```
Respuesta: (body vacío) — `HTTP_STATUS: 204`

Verificación en DB: `usuario.agencia_id` de Agente C = `NULL`. ✅

**Resultado: PASS.**

---

## Casos de error adicionales (sección 6 del checklist de testing manual)

| Caso | Comando | Resultado |
|---|---|---|
| Sin token | `POST /agencias/` sin header `Authorization` | `401 {"detail":"Missing authentication token"}` |
| Rol incorrecto | `POST /agencias/` con JWT de propietario (requiere agente) | `401 {"detail":"User role is not authorized to perform this operation"}` |
| Recurso inexistente | `POST /agencias/solicitudes/00000000-0000-0000-0000-000000000000/aprobar` | `404 {"detail":"Solicitud 00000000-0000-0000-0000-000000000000 no existe"}` |
| Validación Pydantic | `POST /agencias/` sin `nit` en el body | `422` con detalle de campo faltante (`{"type":"missing","loc":["body","nit"],...}`) |

Todos los códigos de estado y contratos de error coinciden con lo documentado en el docstring de `agencias/infrastructure/api/router.py` y con `specs/agencias/spec.md`.

---

## Limpieza y verificación post-test

Comandos de limpieza ejecutados (en orden, respetando FKs):

```sql
DELETE FROM inmueble WHERE id IN ('e1111111-1111-1111-1111-111111111111','e2222222-2222-2222-2222-222222222222');
DELETE FROM relacion_agencia_propietario WHERE propietario_id='dddddddd-dddd-dddd-dddd-dddddddddddd';
DELETE FROM solicitud_ingreso_agencia WHERE agente_id IN ('aaaaaaaa-...','bbbbbbbb-...','cccccccc-...');
UPDATE usuario SET agencia_id=NULL WHERE id IN ('aaaaaaaa-...','bbbbbbbb-...','cccccccc-...');
DELETE FROM agencia WHERE id IN ('f51c2aaf-9fdc-42a3-8845-0481d4337afd','8f9e7b1c-2695-4d55-a0ac-727df5c94c79');
DELETE FROM usuario WHERE id IN ('aaaaaaaa-...','bbbbbbbb-...','cccccccc-...','dddddddd-...');
```

Conteos post-limpieza (idénticos al baseline):

| tabla | pre-test | post-test |
|---|---|---|
| `agencia` | 0 | 0 |
| `solicitud_ingreso_agencia` | 0 | 0 |
| `relacion_agencia_propietario` | 0 | 0 |
| `usuario` | 1 | 1 |
| `inmueble` | 0 | 0 |

El único usuario restante es el `demo-owner@test.com` preexistente de HU-001, sin `agencia_id`, exactamente como estaba antes del testing.

## Resultado global

- 10.1 — Backend corriendo, conexión a DB verificada: **PASS**
- 10.2 — Crear agencia + rechazo duplicado: **PASS**
- 10.3 — Solicitud + aprobación de ingreso: **PASS**
- 10.4 — Inicio + confirmación de relación: **PASS**
- 10.5 — Revoke manual + cascada de despublicación: **PASS**
- 10.6 — Segunda agencia, auto-revoke real + cascada: **PASS**
- 10.7 — Rechazo de salida de último agente con relación activa, y éxito tras revocar: **PASS**
- 10.8 — Restauración de la base de datos: **PASS**
- 10.9 — Documentación (este reporte): **PASS**
- 10.10 — Verificación de que el estado coincide con el pre-test: **PASS**

## Hallazgos

Ningún bug bloqueante. Único punto de diseño observado (no bloqueante, no contradice ninguna tarea de `tasks.md`): `confirmar_relacion` no asigna automáticamente `agente_responsable_id` al agente que confirma; queda `null` hasta usar `PATCH /agencias/relaciones/{id}/responsable`. Se documenta como nota para una futura HU/decisión de producto, no se modifica el código.
