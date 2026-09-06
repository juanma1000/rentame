## ADDED Requirements

### Requirement: Contratación de seguro de arrendamiento requiere identidad verificada
El sistema SHALL permitir a un inquilino iniciar la contratación de un seguro de arrendamiento únicamente si su cuenta tiene `identidad_verificada = True`. El sistema NO SHALL llamar al proveedor externo de seguro cuando la identidad no esté verificada.

#### Scenario: Inquilino sin identidad verificada no puede iniciar la contratación
- **GIVEN** un inquilino cuya cuenta no tiene `identidad_verificada = True`
- **WHEN** intenta iniciar la contratación de un seguro de arrendamiento
- **THEN** el sistema rechaza el intento sin llamar al proveedor externo, indicando que la identidad debe verificarse primero

#### Scenario: Inquilino con identidad verificada puede iniciar la contratación
- **GIVEN** un inquilino cuya cuenta tiene `identidad_verificada = True`
- **WHEN** envía la documentación requerida para contratar el seguro
- **THEN** el sistema acepta la solicitud y la envía al proveedor de seguro de arrendamiento

### Requirement: Documentación de soporte no se persiste
El sistema NO SHALL almacenar los documentos de soporte (desprendibles de pago, certificado laboral) en ningún medio propio (base de datos, disco o blob storage). El sistema SHALL actuar como intermediario que reenvía los documentos al proveedor externo y descarta los bytes recibidos inmediatamente después de obtener la respuesta.

#### Scenario: Los bytes de los documentos no quedan almacenados tras la contratación
- **GIVEN** una solicitud de contratación con documentos de soporte adjuntos
- **WHEN** el proveedor responde (aprobada o rechazada)
- **THEN** ninguna tabla ni archivo del sistema contiene los bytes de esos documentos; solo persiste el resultado de la póliza

### Requirement: Resultado modelado como póliza con estado propio
El sistema SHALL registrar el resultado de una contratación como una `PolizaArrendamiento` con estado (`pendiente`, `aprobada`, `rechazada`, `activa`, `vencida`), prima mensual y vigencia — no como un evento puntual sin continuidad. El sistema SHALL exponer la prima mensual de forma consultable para que otras capacidades (pago mensual del arrendamiento) puedan calcular retenciones sobre ella.

#### Scenario: Póliza aprobada queda registrada con prima y vigencia
- **GIVEN** una solicitud de contratación enviada al proveedor
- **WHEN** el proveedor aprueba la póliza
- **THEN** el sistema registra una `PolizaArrendamiento` en estado `aprobada`, con prima mensual, vigencia y la referencia externa devuelta por el proveedor

#### Scenario: Póliza rechazada queda registrada
- **GIVEN** una solicitud de contratación enviada al proveedor
- **WHEN** el proveedor rechaza la póliza
- **THEN** el sistema registra una `PolizaArrendamiento` en estado `rechazada`, con la referencia externa devuelta por el proveedor, sin habilitar al inquilino para continuar

### Requirement: Póliza aprobada habilita continuar hacia la firma del contrato
El sistema SHALL considerar a un inquilino con una `PolizaArrendamiento` en estado `aprobada` o `activa` habilitado para proceder al siguiente paso del proceso de arrendamiento (firma del contrato). La firma electrónica en sí es una capacidad separada, fuera de alcance de esta capacidad.

#### Scenario: Inquilino con póliza aprobada puede continuar el proceso
- **GIVEN** un inquilino con una `PolizaArrendamiento` en estado `aprobada`
- **WHEN** el flujo de arrendamiento consulta si puede proceder a la firma del contrato
- **THEN** el sistema indica que está habilitado para continuar

### Requirement: Notificación a propietario/agente ante aprobación
El sistema SHALL registrar la necesidad de notificar al propietario o agente del inmueble cuando la póliza de un inquilino queda `aprobada` para ese inmueble. La entrega efectiva de esa notificación (canal, formato) corresponde a la infraestructura de notificaciones del proyecto, cuando exista.

#### Scenario: Aprobación de póliza genera una notificación pendiente para el propietario
- **GIVEN** una `PolizaArrendamiento` que pasa a estado `aprobada` para un inmueble determinado
- **WHEN** el sistema procesa esa aprobación
- **THEN** queda registrada la necesidad de notificar al propietario o agente responsable de ese inmueble
