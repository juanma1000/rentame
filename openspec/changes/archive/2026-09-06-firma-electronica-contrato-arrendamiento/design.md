## Context

HU-005 (seguro de arrendamiento) está implementada y produce `PolizaArrendamiento` en estado `aprobada`. El PRD exige que el ciclo completo de arrendamiento se cierre con firma digital de contrato (Ley 527 de 1999), pero ni la generación del contrato ni su firma existen en código todavía — y HU-006 (pago mensual) no puede diseñarse porque su precondición ("arrendamiento activo, contrato firmado") no existe. Se exploró en sesión previa (`/opsx:explore HU-006`, que derivó en explorar primero esta pieza faltante) y se decidió: HU propia (HU-009), Rentame genera el contenido del contrato con un template legal propio, Viafirma gestiona solo el proceso de firma.

Se investigó el proveedor: a diferencia de Docusign/Zoho Sign (firma electrónica genérica global, sin respaldo de entidad certificadora colombiana), Viafirma tiene presencia y contenido legal específico para Colombia (dominio `.com.co`, documentación propia sobre Ley 527/1999) y puede ofrecer firma digital certificada — mayor robustez frente al riesgo que el propio PRD señala ("validez legal de la firma electrónica... no está suficientemente validada antes de construir", línea 83).

## Goals / Non-Goals

**Goals:**
- Nuevo dominio `firma-contrato` con aggregate `Contrato` (estado borrador/enviado_a_firma/firmado/rechazado/expirado), generado por Rentame a partir de un template propio (datos de inmueble, inquilino, propietario, póliza aprobada).
- Puerto `ProveedorFirmaElectronicaPort` con `FakeAdapter` (dev/test, siempre firma) y `ViafirmaAdapter` (prod, contrato exacto pendiente de confirmación comercial).
- Webhook que recibe el resultado de la firma y actúa: `firmado` crea `ArrendamientoActivo`; `rechazado`/`expirado` deja el contrato en ese estado sin acción adicional.
- Nuevo aggregate `ArrendamientoActivo`, gate real para HU-006 (cuando exista) — vincula inquilino + inmueble + contrato + póliza.
- Gate de entrada: solo se puede iniciar la generación de un contrato para un inquilino con `PolizaArrendamiento` en estado `aprobada`.

**Non-Goals:**
- No se implementa HU-006 (pago mensual) — este change solo produce `ArrendamientoActivo` para que HU-006 lo consulte después, mismo principio que `PolizaArrendamiento.prima_mensual` para este dominio.
- No se implementa cancelación automática de la póliza de seguro cuando el contrato se rechaza/expira — decisión tomada en la exploración: la póliza queda huérfana, resolución administrativa fuera de alcance.
- No se valida legalmente (fuera del alcance técnico) si Viafirma satisface el estándar de "firma digital" con entidad certificadora — es una validación de negocio/legal, no de este diseño.
- No se construye UI — no hay todavía pantalla de arrendamiento.
- No se implementa renovación de contrato al vencer los 6 meses mínimos del PRD — el aggregate `ArrendamientoActivo` puede exponer fecha de inicio/fin pero su ciclo de vida post-vencimiento es un change futuro.

## Decisions

**1. Proveedor: Viafirma sobre Docusign/Zoho Sign**
Viafirma tiene presencia y documentación legal específica para Colombia; puede ofrecer firma digital certificada (con entidad de certificación), más robusta legalmente que la firma electrónica genérica de Docusign/Zoho Sign. Mismo criterio que Truora (HU-004) sobre Jumio/Onfido: el jugador especializado en el mercado local gana sobre madurez de API pura cuando hay un riesgo regulatorio real de por medio (el propio PRD lo señala).

**2. `Contrato` genera su contenido en Rentame, no en el proveedor**
Rentame controla el texto legal exacto del contrato (canon, duración mínima 6 meses según el PRD, partes involucradas) mediante un template propio; Viafirma solo recibe el documento generado para gestionar el proceso de firma (envío, tracking, webhook de resultado). Esto evita depender del proveedor para compliance del contenido legal, y mantiene el puerto (`ProveedorFirmaElectronicaPort`) enfocado solo en "firmar un documento dado", más fácil de sustituir después.

**3. `ArrendamientoActivo` como aggregate propio, no un estado de `Contrato`**
Mismo principio que llevó a modelar `PolizaArrendamiento` como aggregate propio en vez de un resultado puntual (HU-005 design.md decisión 2): "documento firmado" (`Contrato`) y "relación de arrendamiento en curso" (`ArrendamientoActivo`) son conceptos distintos con ciclos de vida distintos. HU-006 consulta `ArrendamientoActivo`, no `Contrato` — evita que el dominio de pagos tenga que entender los estados internos de la firma.

**4. Póliza huérfana ante rechazo/expiración, sin cancelación automática**
Decisión tomada en la exploración: cancelar una póliza ante Sura es una operación con costo/proceso propio de la aseguradora, no meramente técnica. Se acepta el trade-off de dejarla aprobada sin arrendamiento asociado; resolverla es una operación administrativa (o un change de mantenimiento futuro), no de este diseño.

**5. Gate de póliza aprobada aplicado aquí, no solo documentado**
A diferencia del gate hacia HU-005/006 desde `identidad` (que quedó solo documentado porque `seguro_arrendamiento` no existía aún), acá el gate SÍ se implementa: `seguro_arrendamiento` ya existe, por lo que este dominio puede depender de `PolizaArrendamiento.estado == aprobada` de forma concreta (lectura vía puerto propio, sin acoplarse a la infraestructura de `seguro_arrendamiento` — mismo patrón que `UsuarioIdentidadPort` de ese dominio para leer `identidad_verificada`).

## Flujo (secuencia)

```
Inquilino       Frontend      backend/firma-contrato    ProveedorFirmaElectronicaPort   backend/seguro_arrendamiento
   │                │                  │                          │                              │
   │                │ POST /firma-contrato/generar               │                              │
   │                ├─────────────────>│                          │                              │
   │                │                  │ verifica poliza.estado==aprobada                        │
   │                │                  ├──────────────────────────────────────────────────────────>│
   │                │                  │<──────────────────────────────────────────────────────────┤
   │                │                  │ (si no aprobada: rechaza sin generar documento)           │
   │                │                  │ genera Contrato (template propio, estado=borrador)        │
   │                │                  │ enviar_a_firma(documento)                                 │
   │                │                  ├─────────────────────────>│                                │
   │                │                  │                          │ (Fake: firma inmediato)        │
   │                │                  │                          │ (Viafirma: async, webhook luego)│
   │                │                  │<─────────────────────────┤                                │
   │                │                  │ Contrato.estado = enviado_a_firma                          │
   │                │<─────────────────┤                          │                                │
   │                │ 200 { estado: "enviado_a_firma" }           │                                │
   │<───────────────┤                  │                          │                                │
   .                .                  .                          .                                .
   │                │                  │ POST /firma-contrato/webhook (Viafirma)                   │
   │                │                  │<─────────────────────────┤                                │
   │                │                  │ si firmado: Contrato.estado=firmado                        │
   │                │                  │             + crea ArrendamientoActivo                     │
   │                │                  │ si rechazado/expirado: Contrato.estado=ese, sin más acción  │
```

## Estrategia de testing

- **`Contrato` (domain)**: unit tests puros — creación en `borrador`, transición a `enviado_a_firma`/`firmado`/`rechazado`/`expirado`, invariante de que un contrato `firmado` no puede volver a `enviado_a_firma`.
- **`ArrendamientoActivo` (domain)**: unit tests — creación solo posible a partir de un `Contrato` en estado `firmado`.
- **`FakeAdapter`**: unit test — siempre retorna resultado `firmado` con `referencia_externa` determinística.
- **Caso de uso `generar_contrato` (application)**: tests con `FakeAdapter` inyectado — inquilino sin `PolizaArrendamiento` aprobada es rechazado SIN generar documento ni llamar al proveedor; inquilino con póliza aprobada genera contrato y lo envía a firma.
- **Caso de uso `procesar_resultado_firma` (application, invocado por el webhook)**: tests — resultado `firmado` marca el contrato y crea `ArrendamientoActivo`; resultado `rechazado`/`expirado` marca el contrato sin crear nada más ni tocar la póliza.
- **Endpoint `POST /firma-contrato/generar` (infrastructure/api)**: tests de integración — sin póliza aprobada retorna error explícito; con póliza aprobada retorna 200 con estado `enviado_a_firma`.
- **Endpoint `POST /firma-contrato/webhook` (infrastructure/api)**: tests de integración — payload de Viafirma simulado para cada resultado (firmado/rechazado/expirado), verifica el efecto correcto en `Contrato`/`ArrendamientoActivo`.
- **`ViafirmaAdapter`**: tests con HTTP client mockeado — mapeo de respuesta al enviar a firma; manejo de timeout/error sin 500 (estado explícito "envío a firma no disponible").
- Cobertura mínima 80% en `domain/` y `application/`, igual que el resto del proyecto.

## Risks / Trade-offs

- **[Riesgo] Viafirma no confirmado comercialmente (contrato/API exacta pendiente)** → Mitigación: puerto agnóstico + `FakeAdapter` permite avanzar; `ViafirmaAdapter` real queda como open question explícito, mismo patrón que `TruoraAdapter`/`SuraAdapter`.
- **[Riesgo] Firma asíncrona vía webhook introduce estado intermedio (`enviado_a_firma`) sin garantía de cuándo llega el resultado** → Mitigación: el contrato queda visible en ese estado; no se bloquea nada más del sistema mientras tanto (no hay timeout automático a `expirado` implementado en este change — Viafirma es quien determina la expiración y la reporta vía webhook).
- **[Trade-off] Póliza huérfana ante rechazo/expiración, sin cancelación automática** → Aceptado en la exploración: evita acoplar este dominio a operaciones de cancelación de `seguro_arrendamiento`, a costa de dejar pólizas aprobadas sin uso real hasta que alguien las resuelva manualmente.
- **[Riesgo] Validez legal de Viafirma como "firma digital certificada" no verificada técnicamente en este change** → Es una validación de negocio/legal (contactar a Viafirma, confirmar si ofrece entidad certificadora para Colombia), no bloquea el diseño técnico porque el puerto es agnóstico al nivel de certificación que finalmente se contrate.

## Migration Plan

1. Migración Alembic: crear tabla `contratos` (usuario_id FK, poliza_id FK, estado, documento_referencia, referencia_externa) y tabla `arrendamientos_activos` (usuario_id FK, contrato_id FK, inmueble_id, fecha_inicio, estado).
2. Deploy con `FakeAdapter` como default en todos los ambientes hasta confirmar contrato/credenciales de Viafirma en producción — mismo mecanismo de configuración por ambiente que `identidad`/`seguro_arrendamiento`.
3. Rollback: dropear ambas migraciones (tablas nuevas, sin alterar tablas existentes) y remover el paquete `firma_contrato/`; ningún dominio existente depende de este código (solo lee `PolizaArrendamiento`, no lo modifica).

## Open Questions

- Contrato exacto de integración con Viafirma (endpoint, payload, si requiere entidad certificadora contratada aparte) — no bloquea el resto del diseño porque el puerto ya está definido independiente del proveedor.
- Timeout/expiración automática de un contrato en `enviado_a_firma` sin respuesta del proveedor — no se implementa en este change; depende de si Viafirma reporta expiración vía webhook o si Rentame necesita un job propio.
- Relación exacta entre `ArrendamientoActivo` y el inmueble (¿bloquea el inmueble para nuevas solicitudes mientras esté activo?) — corresponde a la capacidad `inmuebles` o a un change de integración posterior.
