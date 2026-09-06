## Context

HU-009 (firma electrónica) está implementada y produce `ArrendamientoActivo`. El PRD exige que el inquilino pague la mensualidad dentro de la plataforma; hoy no existe ningún mecanismo de cobro, y HU-006 tenía tres puntos abiertos críticos: proveedor de pasarela, modelo pull/push, y mecánica de split de pagos (dado que HU-005 ya decidió que el propietario paga la prima del seguro, retenida del pago del inquilino). Se exploraron los tres en sesión previa (`/opsx:explore HU-006`) y se resolvieron: **Wompi**, **pull**, **split nativo vía la API de pagos a terceros de Wompi**.

Esta HU introduce una pieza nueva que los tres dominios anteriores no tuvieron: un **job programado** (generar el `Pago` pendiente al inicio de cada ciclo mensual). El proyecto ya resolvió un problema análogo — el commit reciente de infra (`infra/aws/migrations-task/`) documenta explícitamente que "Autoscaled deploys (App Runner) run multiple backend replicas concurrently; running alembic on every container start races against the same database. Migrations now run as a separate one-off Fargate task in CI instead." Un scheduler embebido en el proceso de la app (ej. APScheduler) tendría el mismo problema: cada réplica generaría pagos duplicados. Este change reutiliza el mismo patrón de tarea one-off separada.

## Goals / Non-Goals

**Goals:**
- Nuevo dominio `pagos` con aggregate `Pago` (estado pendiente/completado/fallido), vinculado a un `ArrendamientoActivo`.
- Job mensual (tarea ECS/Fargate one-off, mismo patrón que `migrations-task`) que genera un `Pago` pendiente por cada `ArrendamientoActivo` activo, con monto = `PolizaArrendamiento.prima_mensual` implícito en el split (el monto que ve/paga el inquilino es el canon completo del arriendo; el split lo resuelve Wompi en la transacción).
- Puerto `PasarelaPagosPort` con `FakeAdapter` (dev/test, siempre completa) y `WompiAdapter` (prod, contrato exacto pendiente de confirmación comercial).
- Endpoint para que el inquilino inicie el pago de un `Pago` pendiente (pull) + webhook que recibe el resultado de Wompi.
- Historial de pagos por `ArrendamientoActivo`, consultable en cualquier estado.

**Non-Goals:**
- No se implementa débito automático (push) — el inquilino siempre inicia el pago.
- No se implementa lógica propia de custodia/giro de fondos — el split lo ejecuta Wompi como parámetro de la transacción; Rentame nunca retiene el dinero del propietario en una cuenta propia.
- No se implementa notificación real al propietario cuando el pago se procesa — documentado como requirement, sin infraestructura de notificaciones (mismo tratamiento que HU-005).
- No se implementa gestión de mora, penalidades por atraso, ni reintentos automáticos de un pago fallido — el `Pago` queda en estado `fallido`, consultable, y el inquilino puede iniciar un nuevo intento manualmente (no está más detallado en este change).
- No se construye UI — no hay todavía pantalla de arrendamiento activo.

## Decisions

**1. Proveedor: Wompi sobre PayU/ePayco**
Wompi (Bancolombia) tiene la API descrita como más moderna del mercado colombiano, y publica una "Pagos a Terceros API" que encaja directo con la necesidad de este dominio: cobrar al inquilino y dividir automáticamente el desembolso entre Rentame (retiene la prima) y el propietario (recibe el neto). PayU tiene oferta de marketplace más consolidada operativamente pero integración más pesada; ePayco no muestra señal de split nativo. Mismo criterio de especialización local ya aplicado a Truora/Sura/Viafirma.

**2. Pull sobre push (débito automático)**
El inquilino inicia el pago manualmente cada ciclo. Evita la complejidad de tokenizar métodos de pago recurrentes, manejar reintentos automáticos de débito, y las implicaciones de compliance (PCI) de guardar credenciales de pago — apropiado para un MVP. Push queda como mejora futura si la mora resulta ser un problema real en producción.

**3. Split ejecutado por Wompi, no por lógica propia de Rentame**
Decisión tomada en la exploración: si Rentame recibiera el pago completo y girara el neto después con un proceso propio, pasaría a custodiar fondos de terceros — con implicaciones regulatorias y financieras mayores (posible necesidad de estar vigilado como manejador de recursos). Ejecutar el split como parámetro nativo de la transacción de Wompi mantiene a Rentame fuera de esa categoría.

**4. Job mensual como tarea ECS/Fargate one-off, no un scheduler embebido**
Mismo razonamiento que ya aplicó el equipo a las migraciones de Alembic: el backend corre en múltiples réplicas autoescaladas (App Runner); un scheduler dentro del proceso de la app correría una vez por réplica, generando `Pago`s duplicados para el mismo `ArrendamientoActivo` en el mismo ciclo. Una tarea separada, disparada por schedule externo (EventBridge o equivalente), corre exactamente una vez.

**5. `Pago` vinculado a `ArrendamientoActivo`, no a `Contrato` ni a `PolizaArrendamiento` directamente**
Mismo principio aplicado en los tres dominios anteriores (cada aggregate consulta el aggregate inmediatamente anterior en la cadena, no salta capas): `pagos` lee `ArrendamientoActivo` para saber que existe una relación de arrendamiento vigente, y a través de ella llega a `poliza_id` (para la prima) e `inmueble_id` (para el propietario) cuando arma el split — sin acoplarse directamente a los detalles internos de `Contrato` o de la firma electrónica.

## Flujo (secuencia)

```
Job mensual (ECS one-off)      backend/pagos          PasarelaPagosPort         backend/firma_contrato (lectura)
        │                          │                        │                              │
        │ por cada ArrendamientoActivo activo                │                              │
        ├─────────────────────────────────────────────────────────────────────────────────>│
        │<─────────────────────────────────────────────────────────────────────────────────┤
        │ crea Pago(pendiente, fecha_limite)                 │                              │
        │─────────────────────────>│                        │                              │

Inquilino          Frontend (futuro)     backend/pagos         PasarelaPagosPort (Wompi)
   │                    │                     │                         │
   │ inicia pago        │                     │                         │
   ├───────────────────>│                     │                         │
   │                    │ POST /pagos/{id}/iniciar                      │
   │                    ├────────────────────>│                         │
   │                    │                     │ iniciar_cobro(monto, split: prima->Rentame, resto->propietario)
   │                    │                     ├────────────────────────>│
   │                    │                     │                         │ (Fake: completa inmediato)
   │                    │                     │                         │ (Wompi: async, webhook luego)
   │                    │                     │<────────────────────────┤
   │                    │<────────────────────┤                         │
   │                    │ 200 { estado: ... } │                         │
   │<───────────────────┤                     │                         │
   .                    .                     .                         .
   │                    │                     │ POST /pagos/webhook (Wompi)
   │                    │                     │<────────────────────────┤
   │                    │                     │ si completado: Pago.estado=completado, fecha_pago
   │                    │                     │ si fallido: Pago.estado=fallido
```

## Estrategia de testing

- **`Pago` (domain)**: unit tests puros — creación en `pendiente`, transición a `completado`/`fallido`, invariante de que un pago `completado` no puede volver a `pendiente`.
- **`FakeAdapter`**: unit test — siempre retorna resultado `completado` con `referencia_externa` determinística.
- **Caso de uso `generar_pagos_del_ciclo` (application, invocado por el job)**: tests — genera exactamente un `Pago` pendiente por `ArrendamientoActivo` activo; no genera un segundo `Pago` pendiente si ya existe uno sin resolver para el ciclo actual (idempotencia ante reintentos del job).
- **Caso de uso `iniciar_pago` (application)**: tests con `FakeAdapter` inyectado — arma el split (monto total, prima a retener, neto al propietario) a partir de `ArrendamientoActivo`/`PolizaArrendamiento`/`Inmueble`; un `Pago` ya `completado` no puede reiniciarse.
- **Caso de uso `procesar_resultado_pago` (application, invocado por el webhook)**: tests — resultado `completado` marca el `Pago` con fecha de pago; resultado `fallido` marca el `Pago` sin más efectos.
- **Endpoint `POST /pagos/{id}/iniciar` (infrastructure/api)**: tests de integración — pago inexistente retorna 404; pago ya completado retorna error explícito; pago pendiente válido retorna 200.
- **Endpoint `POST /pagos/webhook` (infrastructure/api)**: tests de integración — payload simulado de Wompi para cada resultado.
- **`WompiAdapter`**: tests con HTTP client mockeado — mapeo de respuesta y del payload de split; manejo de timeout/error sin 500.
- **Job `generar_pagos_del_ciclo` (script/entrypoint de la tarea ECS)**: test de integración que confirma que corre contra la base real y es idempotente si se ejecuta dos veces en el mismo ciclo.
- Cobertura mínima 80% en `domain/` y `application/`, igual que el resto del proyecto.

## Risks / Trade-offs

- **[Riesgo] Wompi no confirmado comercialmente para pagos a terceros (contrato/API exacta pendiente)** → Mitigación: puerto agnóstico + `FakeAdapter` permite avanzar; `WompiAdapter` real queda como open question explícito, mismo patrón que los tres dominios anteriores.
- **[Riesgo] Job mensual duplicando pagos si corre más de una vez en el mismo ciclo** → Mitigación: `generar_pagos_del_ciclo` es idempotente (no crea un segundo `Pago` pendiente si ya existe uno sin resolver para ese `ArrendamientoActivo` en el ciclo actual).
- **[Trade-off] Pull en vez de push deja la mora como un problema no resuelto técnicamente** → Aceptado para MVP; push (débito automático) queda como mejora futura si la tasa de mora lo justifica.
- **[Riesgo] Ausencia de gestión de mora/penalidades** → Fuera de alcance explícito; un pago fallido o no iniciado a tiempo simplemente queda visible en el historial, sin consecuencia automática sobre el `ArrendamientoActivo`.
- **[Trade-off] Notificación a propietario documentada pero no implementada** → Igual que HU-005: no existe infraestructura de notificaciones; implementarla aquí sería prematuro sin el resto del sistema de notificaciones.

## Migration Plan

1. Migración Alembic: crear tabla `pagos` (arrendamiento_activo_id FK, estado, monto, fecha_limite, fecha_pago, referencia_externa).
2. Infra: nueva tarea ECS/Fargate one-off (`infra/aws/pagos-mensuales-task/`, mismo patrón que `migrations-task/`) con su propio schedule (EventBridge), disparando `generar_pagos_del_ciclo` una vez al mes.
3. Deploy con `FakeAdapter` como default en todos los ambientes hasta confirmar contrato/credenciales de Wompi en producción — mismo mecanismo de configuración por ambiente que los tres dominios anteriores.
4. Rollback: dropear la migración (tabla nueva, sin alterar tablas existentes), remover el paquete `pagos/` y la tarea ECS del job mensual; ningún dominio existente depende de este código (solo lee `ArrendamientoActivo`/`PolizaArrendamiento`/`Inmueble`, no los modifica).

## Open Questions

- Contrato exacto de integración con la API de Pagos a Terceros de Wompi (endpoint, payload del split, comisión/retención exacta) — no bloquea el resto del diseño porque el puerto ya está definido independiente del proveedor.
- Duración exacta del ciclo de facturación y cómo se calcula la "fecha límite" de cada `Pago` a partir de `ArrendamientoActivo.fecha_inicio` — se resuelve al implementar `generar_pagos_del_ciclo`, siguiendo la duración mínima de 6 meses ya mencionada en el PRD como referencia de periodicidad mensual.
- Qué pasa con un `ArrendamientoActivo` que acumula varios `Pago` en estado `fallido` consecutivos — corresponde a un change de mantenimiento futuro (mora/penalidades), no a este.
