## Why

Los backends de HU-004 (identidad), HU-005 (seguro), HU-009 (firma electrónica) y HU-006 (pago mensual) están implementados y probados vía `curl`, pero ningún inquilino puede completarlos desde la aplicación real — no existe ninguna pantalla. Hoy la app solo permite publicar/buscar inmuebles y gestionar cuentas/agencias; el caso de uso central del PRD (arrendar un inmueble completo, de forma 100% digital) no es usable end-to-end. Se exploró en sesión previa (`/opsx:explore`, tras notar este hueco) y se decidió construir un wizard de 4 pasos, fiel a los gates ya implementados en el backend.

## What Changes

- Nuevo microfrontend remote `arrendamiento-app` (mismo patrón Module Federation que `inmuebles-app`) con un wizard secuencial de 4 pasos: verificar identidad → contratar seguro → generar y firmar contrato → (arrendamiento activo).
- El wizard fuerza orden estricto — no se puede saltar a un paso cuyo gate previo no está satisfecho, reflejando los gates reales del backend (`IdentidadNoVerificada`, `PolizaNoAprobada`, etc.).
- Punto de entrada: botón "Solicitar arrendamiento" en `InmuebleDetallePublicoPage` (coincide con el diagrama de secuencia 3b ya documentado en `architecture.md`), visible solo para sesiones con `rol == inquilino`; sin sesión, redirige a registro/login y retoma el flujo tras autenticarse.
- **Modificación de backend** (necesaria para que el wizard sepa en qué paso está al cargar/refrescar, dado que hoy solo existen endpoints de acción): se agregan `GET /identidad/estado`, `GET /seguro-arrendamiento/estado` y `GET /firma-contrato/estado`, cada uno devolviendo el estado actual de la cuenta autenticada para ese dominio (sin crear ni modificar nada).
- El historial y la acción de pagar (`GET /arrendamientos/{id}/pagos`, `POST /pagos/{id}/iniciar`, ya existentes) se exponen en una página separada "Mi arrendamiento" del panel del inquilino, no como un quinto paso del wizard — el wizard termina cuando el `ArrendamientoActivo` se crea (firma exitosa); pagar es una acción recurrente posterior, no un paso de onboarding único.
- Se asume (sin forzarlo en backend, ya que no está garantizado por ningún gate) que un inquilino cursa un solo arrendamiento a la vez; el wizard no contempla múltiples arrendamientos simultáneos.
- El backend no tiene ningún paso de aprobación del propietario sobre un inquilino específico (confirmado: ni el PRD ni las specs existentes lo mencionan) — el frontend se construye fiel a eso, sin agregar ese paso.

## Capabilities

### New Capabilities
- `arrendamiento-flujo-ui`: wizard frontend de 4 pasos (identidad, seguro, firma, arrendamiento activo) más la página "Mi arrendamiento" (historial y pago), consumiendo los backends ya existentes de `identidad`/`seguro_arrendamiento`/`firma_contrato`/`pagos`.

### Modified Capabilities
- `identidad`: se agrega el requirement de un endpoint de consulta de estado (`GET /identidad/estado`), sin cambiar el comportamiento de validación ya existente.
- `seguro-arrendamiento`: se agrega el requirement de un endpoint de consulta de estado (`GET /seguro-arrendamiento/estado`).
- `firma-contrato`: se agrega el requirement de un endpoint de consulta de estado (`GET /firma-contrato/estado`).

## Impact

- Backend: tres endpoints GET nuevos, de solo lectura, en los routers ya existentes de `identidad`/`seguro_arrendamiento`/`firma_contrato` — sin nuevas tablas, sin migraciones, sin tocar casos de uso de escritura existentes.
- Frontend: nuevo remote `frontend/arrendamiento-app/` (rspack, Module Federation, expuesto como `arrendamientoApp/ArrendamientoRoutes`); `shell` agrega el remote y una entrada de navegación para inquilinos; `inmuebles-app` agrega el botón "Solicitar arrendamiento" en `InmuebleDetallePublicoPage`. Reutiliza `@rentame/ui` (Button, Input, Badge) y `@rentame/auth` (sesión, rol) ya existentes — sin tocar esos paquetes.
- Fuera de alcance: paso de aprobación del propietario (no existe en el PRD ni en specs previas), soporte de múltiples arrendamientos simultáneos, comprobante de pago descargable, notificaciones al propietario (ya documentadas como pendientes en HU-005/006).
- Rollback: los 3 GET nuevos son aditivos y de solo lectura (revertir es quitar el endpoint sin efecto en datos); el frontend es un remote nuevo, independiente — removerlo (y el botón de entrada en `inmuebles-app`) no afecta ningún flujo existente.
