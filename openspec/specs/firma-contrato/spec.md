# firma-contrato

## Purpose

TBD: gestiona la generación del contrato de arrendamiento, su envío al proveedor de firma electrónica, y la creación del arrendamiento activo cuando el contrato queda firmado.

## Requirements

### Requirement: Generación de contrato requiere póliza aprobada
El sistema SHALL permitir generar un contrato de arrendamiento para un inquilino únicamente si existe una `PolizaArrendamiento` en estado `aprobada` para esa cuenta. El sistema NO SHALL generar ningún documento ni llamar al proveedor de firma cuando no exista una póliza aprobada.

#### Scenario: Inquilino sin póliza aprobada no puede generar contrato
- **GIVEN** un inquilino sin una `PolizaArrendamiento` en estado `aprobada`
- **WHEN** intenta iniciar la generación de un contrato de arrendamiento
- **THEN** el sistema rechaza el intento sin generar ningún documento ni llamar al proveedor de firma

#### Scenario: Inquilino con póliza aprobada genera el contrato
- **GIVEN** un inquilino con una `PolizaArrendamiento` en estado `aprobada`
- **WHEN** solicita generar el contrato de arrendamiento
- **THEN** el sistema genera el documento con un template propio y lo envía al proveedor de firma electrónica

### Requirement: El contenido legal del contrato lo genera Rentame
El sistema SHALL generar el contenido del contrato (partes, canon, duración) usando un template propio de la plataforma. El proveedor de firma electrónica SHALL recibir únicamente el documento ya generado para gestionar su proceso de firma, sin generar el contenido legal.

#### Scenario: El documento enviado a firma es el generado por Rentame
- **GIVEN** un contrato generado a partir del template propio
- **WHEN** se envía al proveedor de firma electrónica
- **THEN** el proveedor recibe el documento tal como fue generado, sin modificar su contenido legal

### Requirement: Resultado modelado como contrato con estado propio
El sistema SHALL registrar el proceso de firma como un `Contrato` con estado (`borrador`, `enviado_a_firma`, `firmado`, `rechazado`, `expirado`). El sistema NO SHALL permitir que un contrato ya `firmado` regrese a un estado anterior.

#### Scenario: Contrato pasa de borrador a enviado a firma
- **GIVEN** un contrato recién generado en estado `borrador`
- **WHEN** se envía al proveedor de firma electrónica
- **THEN** el sistema registra el contrato en estado `enviado_a_firma`

#### Scenario: Un contrato firmado no puede reenviarse a firma
- **GIVEN** un contrato en estado `firmado`
- **WHEN** se intenta reenviarlo al proceso de firma
- **THEN** el sistema rechaza la operación

### Requirement: Contrato firmado crea un arrendamiento activo
El sistema SHALL crear un `ArrendamientoActivo` únicamente cuando un `Contrato` pasa a estado `firmado`, vinculando al inquilino, el inmueble, el contrato y la póliza asociada. Esta entidad es la que otras capacidades (pago mensual del arrendamiento) SHALL consultar para verificar que existe un arrendamiento activo, en vez de consultar el estado del contrato directamente.

#### Scenario: Firma exitosa crea el arrendamiento activo
- **GIVEN** un contrato en estado `enviado_a_firma`
- **WHEN** el proveedor de firma reporta que el documento fue firmado exitosamente
- **THEN** el sistema marca el contrato como `firmado` y crea un `ArrendamientoActivo` vinculado a ese contrato

#### Scenario: Rechazo o expiración no crea un arrendamiento activo
- **GIVEN** un contrato en estado `enviado_a_firma`
- **WHEN** el proveedor de firma reporta rechazo o expiración
- **THEN** el sistema marca el contrato con ese estado y NO crea ningún `ArrendamientoActivo`

### Requirement: Póliza queda huérfana ante rechazo o expiración del contrato
Cuando un contrato es rechazado o expira sin firmarse, el sistema NO SHALL cancelar automáticamente la `PolizaArrendamiento` aprobada asociada. Su resolución es una operación administrativa fuera de esta capacidad.

#### Scenario: La póliza sigue aprobada tras el rechazo del contrato
- **GIVEN** una `PolizaArrendamiento` aprobada y un contrato asociado que es rechazado
- **WHEN** el sistema procesa el rechazo
- **THEN** la `PolizaArrendamiento` permanece en estado `aprobada`, sin ninguna cancelación automática iniciada por el sistema
