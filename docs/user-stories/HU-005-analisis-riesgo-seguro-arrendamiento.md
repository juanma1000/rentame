# HU-005 — Análisis de riesgo o contratación de seguro de arrendamiento

## Historia
Como inquilino,
quiero completar el análisis de riesgo crediticio o la contratación de un seguro de arrendamiento dentro de la plataforma,
para obtener la aprobación necesaria para formalizar el contrato de arrendamiento de forma digital, sin tramitar documentos físicos ni visitar oficinas.

## Criterios de aceptación
- [x] El inquilino puede iniciar el proceso de análisis de riesgo / seguro solo si su identidad fue previamente verificada (HU-004). (gate real implementado, no solo documentado — `identidad_verificada` se lee antes de llamar al proveedor)
- [x] El sistema presenta al inquilino el mecanismo habilitado por la plataforma. (resuelto: **solo seguro de arrendamiento**, ver notas técnicas)
- [x] El inquilino puede adjuntar la documentación requerida por el proceso (ej. desprendibles de pago, certificado laboral) directamente en la plataforma, sin enviarla por canales externos. (backend: proxy multipart sin persistencia, igual que HU-004; UI queda para cuando exista pantalla de arrendamiento)
- [x] El sistema consume la API externa correspondiente (seguro) y devuelve un resultado: aprobado o rechazado. (vía `FakeAdapter` en dev/test; `SuraAdapter` con contrato real pendiente de negociación comercial)
- [x] Si el resultado es aprobado, el sistema habilita al inquilino para proceder a la firma del contrato de arrendamiento. (expuesto por el dominio; la firma en sí es HU propia futura, fuera de alcance)
- [x] Si el resultado es rechazado, el inquilino recibe una notificación con el motivo (en la medida en que la API lo permita) y el proceso se detiene. (resultado y motivo quedan expuestos por el backend; la pantalla en UI es parte de un change de frontend futuro)
- [ ] El propietario o agente recibe una notificación cuando el análisis de riesgo / seguro del inquilino es aprobado para su inmueble. (documentado como requirement en `specs/seguro-arrendamiento/spec.md`; la entrega real depende de infraestructura de notificaciones que no existe todavía en el proyecto)
- [x] El resultado del análisis queda registrado en el sistema con fecha, estado y el inmueble al que aplica. (registrado con fecha y estado; el vínculo a inmueble específico se resuelve cuando exista el flujo de solicitud de arrendamiento — hoy la póliza es por cuenta de usuario)
- [ ] Tras la aprobación, el sistema genera o facilita la firma del contrato de arrendamiento digital con validez legal en Colombia. (fuera de alcance de este change — ver nota técnica sobre firma electrónica como HU propia)

## Notas técnicas
- **Punto abierto crítico resuelto** (decidido en `/opsx:explore HU-06` y `openspec/changes/seguro-arrendamiento-inquilino/design.md`): el mecanismo es **solo seguro de arrendamiento** (no estudio de crédito). Proveedor elegido: **Sura / ArriendeSeguro** — a diferencia de Truora (HU-004), no tiene API pública documentada para desarrolladores; el contrato de integración real queda pendiente de negociación comercial, resuelto en el dominio con un puerto agnóstico (`FakeAdapter` ahora, `SuraAdapter` real después).
- **Quién paga la prima**: el propietario. Se retiene del pago mensual del inquilino antes de girar el neto al propietario (split de pagos) — esto se implementa en HU-006, no en esta HU; `PolizaArrendamiento.prima_mensual` queda expuesta para que HU-006 la consuma.
- La firma del contrato digital (Ley 527 de 1999) se separó como **HU propia**, fuera de alcance de HU-005 — pendiente de numerar y explorar cuando se aborde.
- Esta HU tiene dependencia estricta con HU-004 (identidad verificada, implementada) y es prerequisito para HU-006 (pago mensual, aún no construida).

## Prioridad
Alta

## Estimación
13 — Gigante (26h)
