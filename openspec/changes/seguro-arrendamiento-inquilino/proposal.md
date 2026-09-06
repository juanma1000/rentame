## Why

El PRD (HU-005) exige que el inquilino complete un análisis de riesgo o contratación de seguro antes de poder firmar un contrato de arrendamiento — hoy no existe ningún flujo posterior a HU-004 (identidad verificada), y el PRD dejaba críticamente abierto si el mecanismo es estudio de crédito, seguro, o ambos. Se exploró en sesión previa (`/opsx:explore HU-06`) y se decidió: **solo seguro de arrendamiento**, con prima pagada por el propietario y retenida del pago mensual del inquilino (split de pagos en HU-006). Se construye ahora, aislado, con un `FakeAdapter` — el contrato real con Sura/ArriendeSeguro queda pendiente de negociación comercial, igual que Truora quedó pendiente de contrato exacto en HU-004.

## What Changes

- Nuevo dominio `seguro-arrendamiento`: aggregate `PolizaArrendamiento` con estado propio (pendiente/aprobada/rechazada/activa/vencida), prima mensual y vigencia — vive más allá del momento de aprobación porque HU-006 la consultará cada mes.
- Puerto `ProveedorSeguroArrendamientoPort` con `FakeAdapter` (dev/test, siempre aprueba con prima determinística) y `SuraAdapter` (prod, contrato exacto es open question — Sura/ArriendeSeguro no tiene API pública documentada).
- Endpoint que recibe la documentación requerida (desprendibles de pago, certificado laboral) como proxy hacia el proveedor, sin persistir los documentos — mismo patrón de minimización de datos de `identidad` (HU-004).
- Gate de entrada: solo un inquilino con `identidad_verificada = True` puede iniciar este proceso (documentado como invariante, aplicado aquí porque `identidad` ya existe).
- El resultado aprobado deja al inquilino habilitado para proceder a la firma del contrato — la firma electrónica en sí (Docusign/Viafirma/Zoho Sign, Ley 527/1999) se separa como HU propia, fuera de alcance de este change.
- Notificaciones a propietario/agente cuando la póliza es aprobada quedan documentadas como requirement, pero su implementación (canal de notificación) es responsabilidad de un change transversal futuro — no existe todavía infraestructura de notificaciones en el proyecto.

## Capabilities

### New Capabilities
- `seguro-arrendamiento`: contratación de seguro de arrendamiento del inquilino contra un proveedor externo (Sura), con resultado modelado como una `PolizaArrendamiento` (estado, prima, vigencia), documentos requeridos manejados como proxy sin persistencia, y gate de entrada sobre identidad verificada.

## Impact

- Backend: nuevo paquete `backend/seguro-arrendamiento/` (domain/application/infrastructure, mismo patrón hexagonal que `identidad`/`agencias`/`inmuebles`/`usuarios`); migración Alembic para tabla `polizas_arrendamiento`; nueva dependencia HTTP hacia Sura (solo en `SuraAdapter`, no en dev/test); lectura de `usuario.identidad_verificada` (dominio `usuarios`, ya existente) como precondición, sin modificarlo.
- Frontend: sin cambio en esta iteración — no hay todavía pantalla de arrendamiento; se documenta pero no se construye UI hasta que exista el flujo completo (HU-005 + firma electrónica + HU-006).
- Fuera de alcance: firma electrónica (HU propia futura), pago mensual y split de retención de prima (HU-006, que consumirá `PolizaArrendamiento.prima_mensual` cuando exista), canal de notificaciones a propietario/agente.
- Rollback: feature aislada y aditiva (nueva tabla, sin tocar dominios existentes salvo lectura); revertir es dropear la migración y el paquete `seguro-arrendamiento/` sin afectar `identidad`/`usuarios`/`agencias`/`inmuebles`.
