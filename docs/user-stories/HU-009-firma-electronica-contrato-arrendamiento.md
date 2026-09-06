# HU-009 — Firma electrónica del contrato de arrendamiento

## Historia
Como inquilino,
quiero firmar electrónicamente el contrato de arrendamiento dentro de la plataforma una vez mi seguro de arrendamiento fue aprobado,
para completar el ciclo de arrendamiento de forma 100% digital, con validez legal en Colombia (Ley 527 de 1999), sin firma física.

## Criterios de aceptación
- [x] El inquilino puede iniciar la generación del contrato de arrendamiento solo si tiene una póliza de seguro de arrendamiento aprobada (HU-005).
- [x] El contenido legal del contrato (partes, canon, duración mínima 6 meses) lo genera la plataforma con un template propio, no el proveedor de firma.
- [x] El sistema envía el documento generado a un proveedor externo de firma electrónica y registra el proceso con estado propio (borrador, enviado a firma, firmado, rechazado, expirado).
- [x] Un contrato ya firmado no puede volver a enviarse al proceso de firma.
- [x] Cuando el contrato se firma exitosamente, el sistema crea un arrendamiento activo vinculado a ese contrato, que otras capacidades (pago mensual) podrán consultar como gate.
- [x] Si el contrato se rechaza o expira sin firmarse, el sistema no crea ningún arrendamiento activo.
- [x] Si el contrato se rechaza o expira, la póliza de seguro aprobada asociada no se cancela automáticamente — queda como una resolución administrativa fuera de esta capacidad.

## Notas técnicas
- Esta HU no estaba numerada en el PRD original — la firma electrónica se mencionaba como parte del ciclo dentro de HU-005, pero se decidió separarla como HU propia (`/opsx:explore HU-006`, que derivó en explorar primero esta pieza faltante) porque es una integración técnica independiente (webhook de firma, estados de contrato) con su propio diseño.
- Proveedor elegido: **Viafirma** — a diferencia de Docusign/Zoho Sign (firma electrónica genérica global, sin respaldo de entidad certificadora colombiana), tiene presencia y contenido legal específico para Colombia y puede ofrecer firma digital certificada, mitigando el riesgo que el propio PRD señala ("validez legal de la firma electrónica... no está suficientemente validada antes de construir"). El contrato exacto de integración queda pendiente de negociación comercial, resuelto en el dominio con un puerto agnóstico al proveedor (`FakeAdapter` en dev/test, `ViafirmaAdapter` real).
- Dependencia estricta con HU-005 (póliza de seguro aprobada, implementada) y es prerequisito de HU-006 (pago mensual, aún no construida) — HU-006 consultará el `ArrendamientoActivo` que produce esta capacidad como gate, en vez del contrato directamente.
- Fuera de alcance: el concepto de "solicitud de arrendamiento" (elegir un inmueble concreto y solicitarlo) no existe todavía — hoy el gate de esta capacidad es tener una póliza aprobada, sin vincular la generación del contrato a un flujo previo de selección de inmueble explícito en el código.

## Prioridad
Alta

## Estimación
08 — Muy Grande (17h)
