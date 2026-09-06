# identidad

## Purpose

TBD: valida la identidad de un inquilino mediante su cédula colombiana contra un proveedor externo, y expone el resultado como un dato permanente de la cuenta.

## Requirements

### Requirement: Validación de identidad vía cédula colombiana
El sistema SHALL permitir a un inquilino iniciar un proceso de validación de identidad indicando su número de cédula de ciudadanía colombiana y adjuntando o capturando la imagen del documento (frente y dorso), desde su perfil o desde el flujo de solicitud de arrendamiento.

#### Scenario: Inquilino inicia validación con cédula e imágenes
- **GIVEN** un inquilino autenticado sin validación de identidad previa
- **WHEN** envía su número de cédula junto con las imágenes de frente y dorso del documento
- **THEN** el sistema acepta la solicitud y la envía al proveedor de validación de identidad

### Requirement: Resultado de validación contra proveedor externo
El sistema SHALL consumir un proveedor externo de validación de identidad (Truora en producción) y SHALL registrar el resultado como `aprobado` o `rechazado`, junto con la fecha y una referencia externa del proveedor.

#### Scenario: Validación aprobada queda registrada
- **GIVEN** una solicitud de validación enviada al proveedor
- **WHEN** el proveedor responde que la identidad es válida
- **THEN** el sistema registra una `ValidacionIdentidad` en estado `aprobado`, con fecha y la referencia externa devuelta por el proveedor

#### Scenario: Validación rechazada queda registrada
- **GIVEN** una solicitud de validación enviada al proveedor
- **WHEN** el proveedor responde que la identidad no pudo ser confirmada
- **THEN** el sistema registra una `ValidacionIdentidad` en estado `rechazado`, con fecha y la referencia externa devuelta por el proveedor

### Requirement: Imágenes del documento no se persisten
El sistema NO SHALL almacenar las imágenes del documento de identidad en ningún medio propio (base de datos, disco o blob storage). El sistema SHALL actuar como intermediario que reenvía las imágenes al proveedor externo y descarta los bytes recibidos inmediatamente después de obtener la respuesta.

#### Scenario: Los bytes de la imagen no quedan almacenados tras la validación
- **GIVEN** una solicitud de validación con imágenes de frente y dorso
- **WHEN** el proveedor responde (aprobado o rechazado)
- **THEN** ninguna tabla ni archivo del sistema contiene los bytes de esas imágenes; solo persiste el resultado, la fecha y la referencia externa

### Requirement: Una sola validación exitosa por cuenta
El sistema SHALL permitir una única validación de identidad aprobada por cuenta de usuario. Una vez aprobada, el sistema NO SHALL permitir ni requerir una nueva validación para solicitudes de arrendamiento posteriores.

#### Scenario: Cuenta ya verificada no puede iniciar una nueva validación aprobada
- **GIVEN** un inquilino cuya cuenta ya tiene una validación de identidad aprobada
- **WHEN** intenta iniciar un nuevo proceso de validación
- **THEN** el sistema rechaza el intento sin llamar al proveedor externo, indicando que la cuenta ya está verificada

### Requirement: Gate de arrendamiento sobre identidad verificada
El sistema SHALL exigir que un inquilino tenga su identidad verificada (`identidad_verificada = True`) antes de poder iniciar una solicitud de arrendamiento formal. Esta capacidad expone el dato y la regla; su aplicación concreta sobre el flujo de solicitud de arrendamiento corresponde a la capacidad que implemente ese flujo (HU-005/HU-006).

#### Scenario: Cuenta sin identidad verificada no puede iniciar solicitud de arrendamiento
- **GIVEN** un inquilino cuya cuenta no tiene `identidad_verificada = True`
- **WHEN** el flujo de solicitud de arrendamiento consulta este dato antes de permitir avanzar
- **THEN** el sistema reporta que la identidad no está verificada, sin permitir continuar
