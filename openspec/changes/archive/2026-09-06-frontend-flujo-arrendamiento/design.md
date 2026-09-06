## Context

Los 4 dominios backend del flujo de arrendamiento (`identidad`, `seguro_arrendamiento`, `firma_contrato`, `pagos`) están implementados y probados, pero sin ninguna UI — se verificaron solo con `curl` en cada change. Al revisar el estado del proyecto (`¿falta algo de front?`) se confirmó que la app hoy solo cubre publicación/búsqueda de inmuebles y gestión de cuentas/agencias; el caso de uso central del PRD (arrendar un inmueble completo, 100% digital) no es usable por una persona real todavía.

Se exploró el diseño de este frontend (`/opsx:explore`) y surgieron dos hallazgos que cambiaron el alcance:

1. **Ningún backend expone estado consultable** (`identidad`/`seguro_arrendamiento`/`firma_contrato` solo tienen endpoints de acción — `POST /validar`, `POST /contratar`, `POST /generar`). Un wizard que sobrevive un refresh de página necesita poder preguntar "¿en qué paso estoy?" sin depender de leer códigos de error de una acción. Se decidió agregar 3 endpoints `GET /estado` como parte de este mismo change (infraestructura habilitante, no tiene sentido aislarla).
2. **No existe aprobación del propietario sobre un inquilino específico** — se confirmó revisando el PRD completo y las specs de HU-005/HU-009: el inquilino pasa los gates (identidad verificada, póliza aprobada) y firma directamente. Se decidió construir el frontend fiel a esto, sin agregar ese paso.

También se confirmó que `PolizaArrendamiento` y `ValidacionIdentidad` son por cuenta (no por inmueble) — el primer punto donde aparece un inmueble concreto es `Contrato`. El backend no impide que un inquilino inicie contratos para más de un inmueble en paralelo; se asume "uno a la vez" solo como convención de UX de este wizard, no como invariante garantizada.

## Goals / Non-Goals

**Goals:**
- Nuevo microfrontend `arrendamiento-app` (Module Federation, mismo patrón que `inmuebles-app`) con un wizard de 4 pasos en orden estricto: identidad → seguro → firma → arrendamiento activo.
- Botón "Solicitar arrendamiento" en `InmuebleDetallePublicoPage`, visible solo para `rol == inquilino`, que redirige a login/registro si no hay sesión (coincide con el diagrama de secuencia 3b ya documentado).
- Tres endpoints `GET /estado` nuevos (identidad, seguro, firma-contrato) que el wizard consulta al montar cada paso para saber si ya está satisfecho, en progreso, o pendiente.
- Página "Mi arrendamiento" separada del wizard — historial de pagos y botón de pago, alimentada por los endpoints de `pagos` ya existentes.

**Non-Goals:**
- No se agrega aprobación del propietario — confirmado que no existe en el alcance del PRD.
- No se soporta más de un arrendamiento simultáneo en la UI — asumido, no forzado por backend.
- No se implementa comprobante de pago descargable ni notificaciones al propietario — ya documentados como pendientes en HU-005/HU-006, sin cambios aquí.
- No se modifica ningún caso de uso de escritura existente en `identidad`/`seguro_arrendamiento`/`firma_contrato` — los 3 endpoints nuevos son de solo lectura.

## Decisions

**1. Un solo remote `arrendamiento-app`, no uno por dominio backend**
Los 4 pasos son un recorrido secuencial de la misma persona en la misma sesión de uso — separarlos en 4 microfrontends que se llaman entre sí agregaría complejidad de Module Federation sin beneficio claro. Mismo criterio que agrupó varias páginas relacionadas de HU-001/002/003 en un solo `inmuebles-app`.

**2. Endpoints `GET /estado` agregados en este change, no aislados**
Son infraestructura habilitante específica para este frontend — sin un consumidor, no tienen razón de existir por separado. Se agregan como `MODIFIED` (nuevo requirement) sobre las specs `identidad`/`seguro-arrendamiento`/`firma-contrato` ya existentes, no como una nueva capability.

**3. Wizard de orden estricto, reflejando los gates reales del backend**
Un paso no se muestra habilitado si su precondición no está satisfecha (ej. no se puede ver el paso de firma sin `PolizaArrendamiento` aprobada) — evita que el inquilino intente una acción que el backend va a rechazar de todas formas con un error que no tiene traducción amigable todavía.

**4. Pagos vive en una página separada, no como paso 5 del wizard**
El wizard es un flujo de onboarding que termina cuando existe `ArrendamientoActivo` (evento único). Pagar es una acción recurrente mensual — mezclarla como "último paso" del wizard confundiría un evento de una sola vez con una obligación continua. "Mi arrendamiento" es la página natural para ver el arrendamiento activo, su historial de pagos, y pagar el pendiente actual.

**5. Restricción por rol vía `useAuth()` ya existente, sin tocar `@rentame/auth`**
El paquete ya decodifica `rol` del JWT (`auth.types.ts`). El botón "Solicitar arrendamiento" y las rutas del wizard se gatean con `rol === 'inquilino'` directamente en `arrendamiento-app`/`inmuebles-app`, sin necesitar un nuevo componente de guard compartido.

**6. Contrato de los `GET /estado`**
Cada uno devuelve, para el usuario autenticado (via JWT):
- `GET /identidad/estado` → `{ estado: "no_iniciado" | "pendiente" | "aprobado" | "rechazado" }`
- `GET /seguro-arrendamiento/estado` → `{ estado: "no_iniciado" | "pendiente" | "aprobada" | "rechazada", primaMensual?: number }`
- `GET /firma-contrato/estado` → `{ estado: "no_iniciado" | "borrador" | "enviado_a_firma" | "firmado" | "rechazado" | "expirado", arrendamientoActivoId?: string }`

`no_iniciado` es un estado sintético de la capa API (no existe como tal en el dominio) para cuando el usuario no tiene ningún registro todavía — se infiere en el caso de uso nuevo (`consultar_estado`) a partir de "no se encontró ninguna `ValidacionIdentidad`/`PolizaArrendamiento`/`Contrato` para este usuario", sin crear un estado nuevo en los aggregates existentes.

## Flujo (secuencia)

```
Inquilino          InmuebleDetallePublicoPage      arrendamiento-app          backend (4 dominios)
   │                        │                            │                          │
   │ "Solicitar arrendamiento"                            │                          │
   ├───────────────────────>│                             │                          │
   │                        │ verifica sesión + rol       │                          │
   │                        │ (sin sesión → redirige login/registro)                 │
   │                        ├────────────────────────────>│                          │
   │                        │                             │ GET /identidad/estado    │
   │                        │                             ├─────────────────────────>│
   │                        │                             │<─────────────────────────┤
   │                        │                             │ si no aprobado: muestra paso 1
   │                        │                             │ si aprobado: GET /seguro-arrendamiento/estado
   │                        │                             ├─────────────────────────>│
   │                        │                             │ ... (mismo patrón para firma) ...
   │                        │                             │ si firmado: arrendamientoActivoId presente
   │                        │                             │ → redirige a "Mi arrendamiento"
```

## Estrategia de testing

- **Backend — `consultar_estado_identidad`/`consultar_estado_seguro`/`consultar_estado_firma` (application, nuevos)**: tests unitarios — sin registro devuelve `no_iniciado`; con registro devuelve su estado real; nunca llama a un proveedor externo (son de solo lectura).
- **Backend — `GET /identidad/estado`, `GET /seguro-arrendamiento/estado`, `GET /firma-contrato/estado` (infrastructure/api)**: tests de integración — requieren inquilino autenticado; devuelven la forma esperada en cada estado.
- **Frontend — `arrendamiento-app` servicios (`identidadService.ts`, `seguroService.ts`, `firmaService.ts`, `pagosService.ts`)**: tests unitarios (Jest) — mapeo correcto de la respuesta del backend al tipo TS, manejo de error de red.
- **Frontend — páginas del wizard**: tests RTL por paso — no habilita el siguiente paso si el estado no lo permite; muestra el estado correcto al montar; envía el formulario y refleja el resultado.
- **Frontend — botón "Solicitar arrendamiento"**: tests RTL — no visible para `rol != inquilino`; redirige a login si no hay sesión; navega al wizard si hay sesión de inquilino.
- **Frontend — "Mi arrendamiento"**: tests RTL — muestra historial completo; botón de pago solo visible si hay un `Pago` pendiente.
- **E2E (Playwright MCP, obligatorio)**: recorrido completo real — publicar inmueble (o usar uno sembrado) → inquilino hace clic en "Solicitar arrendamiento" → completa los 4 pasos con `FakeAdapter`s (siempre aprueban) → llega a "Mi arrendamiento" → inicia y completa un pago (webhook simulado) → historial lo refleja.
- Cobertura mínima 80% en frontend y backend, igual que el resto del proyecto.

## Risks / Trade-offs

- **[Riesgo] Estado sintético `no_iniciado` no existe en el dominio, solo en la capa de consulta** → Mitigación: se documenta explícitamente como inferencia del caso de uso (ausencia de registro), no como un estado nuevo de `ValidacionIdentidad`/`PolizaArrendamiento`/`Contrato` — evita ensuciar los aggregates existentes por una necesidad puramente de UI.
- **[Riesgo] Múltiples arrendamientos simultáneos no bloqueados por backend** → Aceptado: el wizard asume uno a la vez por convención de UX; si en el futuro se necesita bloquear de verdad, es un cambio de dominio en `firma_contrato`, fuera de alcance aquí.
- **[Trade-off] Ausencia de aprobación del propietario puede sorprender a un propietario real** → Fuera de alcance por decisión explícita (no está en el PRD); si se decide agregarla después, afecta a `firma_contrato` (nuevo gate) antes que a este frontend.
- **[Riesgo] Wizard construido contra 3 `FakeAdapter`s** → Ya validado en cada backend individualmente vía curl; el E2E de este change usa los mismos fakes — el comportamiento contra los proveedores reales (Truora/Sura/Viafirma) sigue siendo open question de cada change anterior, no de este.

## Migration Plan

1. Backend: agregar los 3 endpoints `GET /estado` (sin migración — son de solo lectura sobre tablas existentes).
2. Frontend: crear `frontend/arrendamiento-app/` (rspack, Module Federation), agregar el remote a `shell`, agregar el botón de entrada en `inmuebles-app`.
3. Deploy: sin cambios de infraestructura adicionales — mismo patrón de despliegue que `inmuebles-app`.
4. Rollback: los 3 GET son aditivos (remover el endpoint no afecta nada más); el frontend es un remote nuevo e independiente — remover el remote y el botón de entrada no afecta ningún flujo existente.

## Open Questions

- Copy/textos exactos de cada paso del wizard (mensajes de error, textos de ayuda) — se resuelven al implementar, no bloquean el diseño técnico.
- Si en el futuro se agrega aprobación del propietario, dónde vive esa UI (¿panel del propietario ya existente, o nueva sección?) — fuera de alcance de este change.
