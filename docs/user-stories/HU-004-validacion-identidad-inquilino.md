# HU-004 — Validación de identidad del inquilino

## Historia
Como inquilino,
quiero verificar mi identidad mediante mi cédula de ciudadanía colombiana a través de la plataforma,
para poder avanzar en el proceso de arrendamiento de forma completamente digital, sin presentarme físicamente ni enviar documentos por canales externos.

## Criterios de aceptación
- [x] El inquilino puede iniciar el proceso de validación de identidad desde su perfil o desde el flujo de solicitud de arrendamiento. (backend: `POST /identidad/validar`; UI de perfil/flujo de arrendamiento queda para HU-005/006)
- [x] El proceso solicita como mínimo el número de cédula de ciudadanía colombiana y permite adjuntar o capturar la imagen del documento (frente y dorso).
- [x] El sistema consume una API externa de validación de identidad y devuelve un resultado: aprobado o rechazado.
- [x] Si la validación es aprobada, el perfil del inquilino queda marcado como "Identidad verificada" (`usuario.identidad_verificada = True`) y puede continuar con el proceso de arrendamiento.
- [x] Si la validación es rechazada, el inquilino recibe un mensaje explicativo y no puede avanzar en el proceso hasta resolverlo. (resultado y mensaje quedan expuestos por el backend; la pantalla de rechazo en UI es parte de HU-005/006)
- [ ] Un inquilino no puede iniciar una solicitud de arrendamiento formal sin haber completado exitosamente la validación de identidad. (invariante documentada en `specs/identidad/spec.md`; el guard concreto lo aplica el change que construya HU-005/006, que aún no existe)
- [x] La validación de identidad se realiza una sola vez por cuenta de usuario; no se repite para cada solicitud de arrendamiento posterior.
- [x] El resultado de la validación queda registrado en el sistema con fecha y estado.

## Notas técnicas
- Proveedor de la API de validación de identidad: **Truora**, decidido en `/opsx:explore HU-004` y `openspec/changes/validacion-identidad-inquilino/design.md` — nativo LatAm/Colombia, valida cédula contra Registraduría, menor costo que Jumio/Onfido (KYC global sin ventaja real para este caso de uso).
- Esta HU es un prerrequisito funcional y de seguridad para HU-005 y HU-006. Bloquea el avance del flujo si no se completa.
- Según las restricciones del PRD, la integración debe ser compatible con el marco regulatorio colombiano.
- El manejo de documentos de identidad implica consideraciones de privacidad y protección de datos (Ley 1581 de 2012 en Colombia).

## Prioridad
Alta

## Estimación
08 — Muy Grande (17h)
