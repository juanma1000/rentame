## Context

HU-004 exige verificación de identidad del inquilino vía cédula colombiana antes de permitir solicitudes de arrendamiento. El PRD dejaba abierto el proveedor (Truora/Jumio/Onfido); se exploró en sesión previa (`/opsx:explore HU-004`) y se decidió **Truora**: valida contra Registraduría (no solo OCR+liveness genérico como Jumio/Onfido), menor costo por validación, hecho para LatAm/Colombia. HU-005/HU-006 (el flujo de arrendamiento que consumirá `identidad_verificada`) no existen todavía en el código — este change construye la capacidad de forma aislada, con un adapter fake que permite avanzar sin bloquearse por la ausencia de esos flujos.

Dominios existentes (`agencias`, `inmuebles`, `usuarios`) siguen el patrón hexagonal: `domain/` (aggregates, ports, exceptions), `application/` (casos de uso), `infrastructure/` (persistence, api, adapters). Este change reutiliza el mismo patrón para un dominio nuevo `identidad`.

## Goals / Non-Goals

**Goals:**
- Nuevo dominio `identidad` con aggregate `ValidacionIdentidad`, puerto `ProveedorValidacionIdentidadPort`, y dos adapters (`FakeAdapter` para dev/test, `TruoraAdapter` para prod).
- Endpoint proxy que recibe cédula + imágenes, las reenvía al proveedor, y descarta los bytes tras la respuesta — solo persiste resultado + referencia externa.
- Campo `identidad_verificada` en `Usuario`, marcado una sola vez de forma permanente cuando la validación es aprobada.
- Registro auditable: cada intento de validación (aprobado o rechazado) queda en `validaciones_identidad` con fecha y estado.

**Non-Goals:**
- No se construye UI de flujo de arrendamiento ni el guard clause que bloquea iniciar una solicitud sin identidad verificada — HU-005/006 no existen aún; el invariante queda documentado en la spec de `identidad`, para que ese change futuro lo implemente contra este dominio ya existente.
- No se persisten imágenes del documento en storage propio (ni cifradas): decisión explícita de minimización de datos (Ley 1581 de 2012).
- No se implementa reintento automático tras rechazo en este change — el mensaje explicativo al inquilino es responsabilidad de un change de UI posterior (HU-005/006).

## Decisions

**1. Proveedor: Truora sobre Jumio/Onfido**
Truora valida cédula colombiana contra fuente oficial (Registraduría), con menor costo por check y sin necesidad de compliance internacional que no aplica (target es solo Colombia). Jumio/Onfido son KYC global genérico — cobertura Colombia sin ventaja real sobre Truora para este caso de uso, y significativamente más caros.

**2. Backend como proxy de imágenes, sin persistencia propia**
El frontend sube la imagen al backend; el backend reenvía al proveedor y descarta los bytes inmediatamente después de recibir la respuesta (no llegan a disco ni a blob storage). Alternativa considerada: frontend sube directo al proveedor (SDK del proveedor) — se descartó porque acopla el frontend a Truora específicamente, dificultando un cambio de proveedor futuro. El proxy mantiene esa decisión encapsulada detrás del puerto de dominio.

**3. `identidad` como dominio nuevo, no como extensión de `usuarios`**
El proceso de validación (múltiples intentos posibles, estado propio, referencia externa) es un concepto propio con su propio ciclo de vida — no es un atributo simple de `Usuario`. Sigue el mismo criterio ya aplicado a `agencias` (dominio separado aunque relacionado con `usuarios` vía `agencia_id`). `usuarios` solo gana el flag derivado `identidad_verificada`.

**4. `FakeAdapter` siempre aprueba**
Para desarrollo y tests, simplifica probar el happy path completo del flujo de arrendamiento sin fricción de mockear resultados variables en cada test. Los tests que necesiten cubrir el camino de rechazo lo hacen inyectando un stub propio del puerto (no del `FakeAdapter` compartido), manteniendo el fake de desarrollo simple y predecible.

**5. Validación es de una sola vez por cuenta, sin invalidación**
Una vez `identidad_verificada = True`, no hay método en `Usuario` para revertirlo (mismo patrón que `rol`: fijo tras asignación). Si se necesita revocar por fraude detectado después, es una operación administrativa fuera de alcance de este change.

## Flujo (secuencia)

```
Inquilino          Frontend            backend/identidad         ProveedorValidacionIdentidadPort      backend/usuarios
   │                   │                      │                              │                              │
   │ cédula + fotos    │                      │                              │                              │
   ├──────────────────>│                      │                              │                              │
   │                   │ POST /identidad/validar                             │                              │
   │                   ├─────────────────────>│                              │                              │
   │                   │                      │ validar(cedula, frente, dorso)                              │
   │                   │                      ├─────────────────────────────>│                              │
   │                   │                      │                              │ (Fake: aprueba)              │
   │                   │                      │                              │ (Truora: llama API real)     │
   │                   │                      │<─────────────────────────────┤                              │
   │                   │                      │ ResultadoValidacion(aprobado, referencia_externa)           │
   │                   │                      │ [bytes de imagen descartados aquí, no se persisten]         │
   │                   │                      │ persiste ValidacionIdentidad(estado, fecha, referencia)      │
   │                   │                      ├──────────────────────────────────────────────────────────────>│
   │                   │                      │                              │      marca identidad_verificada=True (si aprobado)
   │                   │<─────────────────────┤                              │                              │
   │                   │ 200 { estado: "aprobado" }                          │                              │
   │<──────────────────┤                      │                              │                              │
```

## Estrategia de testing

- **`ValidacionIdentidad` (domain)**: unit tests puros — creación, transición de estado, invariante de "una sola validación aprobada por cuenta" (no se puede crear una segunda validación aprobada si ya existe una).
- **`ProveedorValidacionIdentidadPort` / `FakeAdapter`**: unit test verificando que `FakeAdapter.validar(...)` siempre retorna `aprobado` con una `referencia_externa` determinística (útil para aserciones en tests de integración).
- **`iniciar_validacion_identidad` (application)**: tests con `FakeAdapter` inyectado — caso aprobado marca `Usuario.identidad_verificada = True`; caso rechazado (vía stub propio del puerto) no marca el flag y persiste el intento igual; segundo intento sobre cuenta ya verificada es rechazado por la aplicación sin llamar al proveedor.
- **Endpoint `POST /identidad/validar` (infrastructure/api)**: tests de integración (TestClient) — payload válido con imágenes retorna 200 y el estado esperado; payload sin cédula o sin imágenes retorna 422; los bytes de imagen no quedan en ninguna tabla ni archivo tras la llamada (test explícito que verifica ausencia de persistencia).
- **`TruoraAdapter`**: tests con HTTP client mockeado (no se llama la API real de Truora en CI) — verifica mapeo correcto de la respuesta de Truora a `ResultadoValidacion`, y manejo de error/timeout de la API externa (no debe crashear con 500, debe propagar un estado explícito de "no se pudo validar").
- Cobertura mínima 80% en `domain/` y `application/` de `identidad`, igual que el resto del proyecto.

## Risks / Trade-offs

- **[Riesgo] Dependencia de disponibilidad de Truora** → Mitigación: `TruoraAdapter` maneja timeout/error explícitamente, sin dejar al inquilino en estado ambiguo; el endpoint retorna un estado claro de "validación no disponible, reintentar" en vez de 500.
- **[Riesgo] Costo por validación en producción** → Fuera de alcance técnico de este change; monitoreo de costo es responsabilidad de negocio/ops, no bloquea el diseño.
- **[Trade-off] No persistir imagen limita auditoría propia** → Se acepta porque la referencia externa de Truora permite re-consultar el resultado ante disputa; se prioriza minimización de datos sobre trazabilidad interna completa.
- **[Riesgo] Invariante de gate hacia HU-005/006 sin código que lo aplique todavía** → Mitigación: queda documentado explícitamente como requirement en `specs/identidad/spec.md`, para que el change que construya HU-005/006 lo implemente contra este dominio ya existente, no lo reinvente.

## Migration Plan

1. Migración Alembic: crear tabla `validaciones_identidad` (usuario_id FK, cedula, estado, fecha, referencia_externa) + columna `identidad_verificada BOOLEAN NOT NULL DEFAULT FALSE` en `usuarios`.
2. Deploy de `backend/identidad/` con `FakeAdapter` como default en todos los ambientes hasta que se confirmen credenciales/contrato de Truora en producción (flag de configuración selecciona el adapter).
3. Rollback: dropear la migración (tabla nueva + columna con default seguro no rompe filas existentes) y remover el paquete `identidad/`; ningún dominio existente depende de este código, por lo que el rollback no tiene efectos colaterales.

## Open Questions

- Contrato exacto de la API de Truora (endpoint, formato de payload, códigos de error) — se resuelve al implementar `TruoraAdapter`, no bloquea el resto del diseño porque el puerto ya está definido independiente del proveedor.
- Mensaje explicativo de rechazo al inquilino (copy, canal) — corresponde a HU-005/006 cuando exista la UI de arrendamiento.
