## Why

El PRD exige que el ciclo de arrendamiento se complete 100% digital, sin firma física (línea 51: "Firma electrónica: El ciclo end-to-end requiere firma de contrato digital válida legalmente en Colombia — Ley 527 de 1999"). Hoy, tras una `PolizaArrendamiento` aprobada (HU-005, implementado), no existe ningún mecanismo para generar y firmar el contrato — es el eslabón que falta entre HU-005 y HU-006 (pago mensual), que exige "arrendamientos activos (contrato firmado exitosamente)" como precondición. Se exploró en sesión previa (`/opsx:explore HU-006`, que derivó en explorar esta pieza faltante primero) y se decidió separarla como HU propia (HU-009), con Rentame generando el contenido del contrato y Viafirma gestionando solo el proceso de firma.

## What Changes

- Nuevo dominio `firma-contrato`: aggregate `Contrato` (borrador → enviado_a_firma → firmado/rechazado/expirado), generado por Rentame a partir de un template propio con los datos del inmueble, inquilino, propietario y la `PolizaArrendamiento` aprobada.
- Puerto `ProveedorFirmaElectronicaPort` con `FakeAdapter` (dev/test, siempre firma) y `ViafirmaAdapter` (prod, contrato exacto pendiente de confirmación comercial — Viafirma elegido por su enfoque específico en Colombia/Ley 527 de 1999 frente a Docusign/Zoho Sign, que ofrecen firma electrónica genérica sin respaldo de entidad certificadora colombiana).
- Webhook que recibe el resultado de la firma (firmado/rechazado/expirado) y actúa en consecuencia.
- Nuevo aggregate `ArrendamientoActivo`, creado únicamente cuando el contrato queda `firmado` — vincula inquilino + inmueble + contrato + póliza. Es la entidad que HU-006 (pago mensual) consultará como gate, en vez de consultar el contrato directamente.
- Si el contrato se rechaza o expira, la `PolizaArrendamiento` asociada queda huérfana (sin `ArrendamientoActivo`) — no se dispara ninguna cancelación automática ante el proveedor de seguro; es una operación administrativa fuera de alcance.
- Gate de entrada: solo se puede generar un contrato para un inquilino con `PolizaArrendamiento` en estado `aprobada`.

## Capabilities

### New Capabilities
- `firma-contrato`: generación del contrato de arrendamiento (template propio de Rentame) y gestión de su firma electrónica vía proveedor externo (Viafirma), con resultado modelado como `Contrato` con estado propio, y creación de `ArrendamientoActivo` al firmarse exitosamente.

## Impact

- Backend: nuevo paquete `backend/firma_contrato/` (domain/application/infrastructure, mismo patrón hexagonal que `seguro_arrendamiento`/`identidad`/`agencias`/`inmuebles`/`usuarios`); migración Alembic para tablas `contratos` y `arrendamientos_activos`; nueva dependencia HTTP hacia Viafirma (solo en `ViafirmaAdapter`); lectura de `PolizaArrendamiento` (dominio `seguro_arrendamiento`, ya existente) como precondición, sin modificarlo.
- Frontend: sin cambio en esta iteración — no hay todavía pantalla de arrendamiento.
- Fuera de alcance: HU-006 (pago mensual, que consumirá `ArrendamientoActivo` cuando exista), cancelación automática de póliza ante contrato rechazado/expirado, renovación de contrato, validación legal externa de la robustez de Viafirma como firma digital certificada (riesgo ya señalado en el PRD, línea 83 — queda como validación de negocio, no técnica).
- Rollback: feature aislada y aditiva (nuevas tablas, sin tocar dominios existentes salvo lectura de `PolizaArrendamiento`); revertir es dropear las migraciones y el paquete `firma_contrato/` sin afectar `seguro_arrendamiento`/`identidad`/`usuarios`/`agencias`/`inmuebles`.
