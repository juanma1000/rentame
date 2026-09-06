## Context

HU-005 exige que el inquilino, ya con identidad verificada (HU-004, implementado), complete un análisis de riesgo o contratación de seguro antes de poder firmar un contrato de arrendamiento. El PRD dejaba críticamente abierto el mecanismo (crédito/seguro/ambos); se exploró en sesión previa (`/opsx:explore HU-06`) y se decidió: **solo seguro de arrendamiento**, prima pagada por el propietario y retenida del pago mensual del inquilino antes de girar el neto (split de pagos que resolverá HU-006). Ni HU-005 ni HU-006 existen en el código todavía; este change construye el dominio de seguro de forma aislada, siguiendo el mismo patrón ya validado con `identidad` (HU-004): puerto agnóstico al proveedor + `FakeAdapter` ahora, adapter real cuando exista contrato comercial confirmado.

Se investigó el proveedor elegido (Sura/ArriendeSeguro) y, a diferencia de Truora, **no tiene API pública documentada para desarrolladores** — es un producto de venta al consumidor final. El adapter real queda como open question explícito, no como implementación confiable hasta negociación comercial.

## Goals / Non-Goals

**Goals:**
- Nuevo dominio `seguro-arrendamiento` con aggregate `PolizaArrendamiento` (estado pendiente/aprobada/rechazada/activa/vencida, prima mensual, vigencia), puerto `ProveedorSeguroArrendamientoPort`, y dos adapters (`FakeAdapter` dev/test, `SuraAdapter` prod).
- Endpoint proxy que recibe documentos requeridos (desprendibles de pago, certificado laboral) y los reenvía al proveedor sin persistirlos — mismo patrón de `identidad`.
- Gate de entrada: solo un inquilino con `usuario.identidad_verificada = True` puede iniciar el proceso.
- `PolizaArrendamiento` expone `prima_mensual` para que HU-006 (cuando exista) pueda calcular la retención sobre el pago del propietario.

**Non-Goals:**
- No se implementa la firma electrónica del contrato — se separa como HU propia (decisión tomada en la exploración), fuera de alcance de este change.
- No se implementa el split de pagos / retención de prima en sí — eso corresponde a HU-006, que leerá `PolizaArrendamiento.prima_mensual` cuando ese dominio exista.
- No se implementa el canal de notificación a propietario/agente cuando la póliza se aprueba — no existe infraestructura de notificaciones en el proyecto; queda documentado como requirement sin implementación.
- No se persisten los documentos adjuntos (desprendibles/certificado laboral) en storage propio.
- No se construye UI — no hay todavía pantalla de arrendamiento que consuma este dominio.

## Decisions

**1. Proveedor: Sura (ArriendeSeguro) sobre Seguros Bolívar**
Sura ya vende un producto "Seguro de Arrendamiento Digital" (ArriendeSeguro) diseñado para venta sin fricción vía canal online sin codeudor, lo que sugiere mayor probabilidad de conseguir integración B2B real. Ninguno de los dos tiene API pública confirmada — la decisión final de contrato depende de negociación comercial fuera de alcance técnico. Seguros Bolívar ofrece cobertura más amplia (integral: servicios/daños/inventario) pero sin señal de producto digital-first.

**2. `PolizaArrendamiento` como aggregate con estado propio, no un resultado puntual**
A diferencia de `ValidacionIdentidad` (HU-004, un evento puntual aprobado/rechazado), el seguro es una relación continua: tiene vigencia, puede vencer, y su prima es un dato que otro dominio (HU-006) necesitará consultar repetidamente. Modelarlo como aggregate con estado (`pendiente`/`aprobada`/`rechazada`/`activa`/`vencida`) evita que HU-006 tenga que reinventar el almacenamiento de la prima por su cuenta.

**3. Prima pagada por el propietario, retenida del pago del inquilino**
Decisión tomada en la exploración: el inquilino paga el arriendo completo; Rentame retiene la prima antes de girar el neto al propietario. Esto NO se implementa en este change (es lógica de HU-006), pero determina que `PolizaArrendamiento` debe exponer `prima_mensual` como campo consultable, no solo internamente.

**4. Firma electrónica separada como HU propia**
Decisión tomada en la exploración: aunque en la práctica "aprobado → firma" ocurre en secuencia inmediata, la integración con un proveedor de firma (Docusign/Viafirma/Zoho Sign) es una pieza técnica independiente (webhook de firma, estados de contrato) que merece su propio diseño. Este change se detiene en "póliza aprobada, inquilino habilitado para proceder a firma" sin implementar la firma en sí.

**5. Documentos como proxy sin persistencia — mismo patrón que `identidad`**
Consistencia con la decisión ya tomada en HU-004: minimización de datos (Ley 1581 de 2012). El backend reenvía los documentos al proveedor y descarta los bytes tras la respuesta.

**6. Gate de identidad verificada aplicado aquí, no solo documentado**
A diferencia del gate hacia HU-005/006 desde `identidad` (que quedó solo documentado porque HU-005 no existía), acá el gate SÍ se implementa en código: `identidad` ya existe, por lo que este dominio puede depender de `usuario.identidad_verificada` de forma concreta (lectura vía puerto, sin acoplarse a la infraestructura de `usuarios`, mismo patrón que `identidad.domain.ports.UsuarioIdentidadRepositoryPort`).

## Flujo (secuencia)

```
Inquilino          Frontend       backend/seguro-arrendamiento    ProveedorSeguroArrendamientoPort    backend/identidad (lectura)
   │                   │                    │                              │                              │
   │ docs (nómina,     │                    │                              │                              │
   │ certificado)      │                    │                              │                              │
   ├──────────────────>│                    │                              │                              │
   │                   │ POST /seguro-arrendamiento/contratar              │                              │
   │                   ├───────────────────>│                              │                              │
   │                   │                    │ verifica identidad_verificada│                              │
   │                   │                    ├─────────────────────────────────────────────────────────────>│
   │                   │                    │<─────────────────────────────────────────────────────────────┤
   │                   │                    │ (si False: rechaza sin llamar al proveedor)                  │
   │                   │                    │ contratar(cedula, documentos)                                │
   │                   │                    ├─────────────────────────────>│                              │
   │                   │                    │                              │ (Fake: aprueba, prima fija)  │
   │                   │                    │                              │ (Sura: contrato real TBD)    │
   │                   │                    │<─────────────────────────────┤                              │
   │                   │                    │ ResultadoPoliza(aprobada, prima_mensual, referencia_externa) │
   │                   │                    │ [bytes de documentos descartados aquí, no se persisten]      │
   │                   │                    │ persiste PolizaArrendamiento(estado, prima, vigencia)         │
   │                   │<───────────────────┤                              │                              │
   │                   │ 200 { estado: "aprobada", prima_mensual: ... }    │                              │
   │<──────────────────┤                    │                              │                              │
```

## Estrategia de testing

- **`PolizaArrendamiento` (domain)**: unit tests puros — creación, transiciones de estado (pendiente→aprobada/rechazada, aprobada→activa→vencida), invariante de que una póliza rechazada no puede activarse.
- **`FakeAdapter`**: unit test — siempre retorna `aprobada` con `prima_mensual` y `referencia_externa` determinísticas.
- **Caso de uso `contratar_seguro_arrendamiento` (application)**: tests con `FakeAdapter` inyectado — inquilino sin `identidad_verificada` es rechazado SIN llamar al proveedor ni al puerto de seguro; inquilino verificado y aprobado crea `PolizaArrendamiento` en estado `aprobada`; rechazo (stub propio del puerto) persiste el intento sin habilitar avance.
- **Endpoint `POST /seguro-arrendamiento/contratar` (infrastructure/api)**: tests de integración — payload válido con documentos retorna 200; payload sin documentos retorna 422; inquilino no verificado retorna 403/409 explícito; test explícito de que los bytes de documentos no quedan persistidos.
- **`SuraAdapter`**: tests con HTTP client mockeado (no se llama la API real en CI) — mapeo de respuesta a `ResultadoPoliza`; manejo de timeout/error sin 500 (estado explícito "contratación no disponible").
- Cobertura mínima 80% en `domain/` y `application/`, igual que el resto del proyecto.

## Risks / Trade-offs

- **[Riesgo] Sura no tiene API pública documentada** → Mitigación: puerto agnóstico al proveedor + `FakeAdapter` permite avanzar el resto del sistema; `SuraAdapter` real queda como open question explícito hasta confirmación comercial, mismo patrón que `TruoraAdapter` en HU-004.
- **[Riesgo] `PolizaArrendamiento.prima_mensual` es un contrato implícito hacia HU-006, que no existe** → Mitigación: el campo se expone ahora con un nombre y tipo estables; cuando se construya HU-006 consume este dominio en vez de reinventar el almacenamiento de la prima.
- **[Trade-off] Notificación a propietario/agente documentada pero no implementada** → Se acepta porque no existe infraestructura de notificaciones en el proyecto; implementarla aquí sería una abstracción prematura sin el resto del sistema de notificaciones.
- **[Riesgo] Vigencia de póliza y su vencimiento a mitad de arrendamiento no se resuelve en este change** → Fuera de alcance: el estado `vencida` se modela en el dominio, pero la lógica de renovación/qué pasa con el arrendamiento activo si la póliza vence es parte de HU-006 o un change de mantenimiento futuro.

## Migration Plan

1. Migración Alembic: crear tabla `polizas_arrendamiento` (usuario_id FK, estado, prima_mensual, vigencia_desde, vigencia_hasta, referencia_externa).
2. Deploy con `FakeAdapter` como default en todos los ambientes hasta confirmar contrato/credenciales de Sura en producción (mismo mecanismo de configuración por ambiente que `identidad`).
3. Rollback: dropear la migración (tabla nueva, sin alterar tablas existentes) y remover el paquete `seguro-arrendamiento/`; ningún dominio existente depende de este código (solo lee `usuarios.identidad_verificada`, no lo modifica).

## Open Questions

- Contrato exacto de integración con Sura (endpoint, payload, costos, si expone API real o requiere un intermediario/broker) — no bloquea el resto del diseño porque el puerto ya está definido independiente del proveedor.
- Qué pasa cuando una póliza vence a mitad de un arrendamiento activo (renovación automática, bloqueo del arrendamiento, aviso al propietario) — corresponde a HU-006 o a un change de mantenimiento posterior.
- Numeración/alcance exacto de la HU de firma electrónica separada — pendiente de definir cuando se explore ese change.
