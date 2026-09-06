# arrendamiento-flujo-ui

## Purpose

TBD: expone en el frontend el flujo de solicitud de arrendamiento como un wizard de 4 pasos secuenciales (identidad, seguro, firma, arrendamiento activo), controlando la navegación según el estado real de los dominios backend, y separa la página "Mi arrendamiento" (arrendamiento activo, historial de pagos) de los pasos del wizard.

## Requirements

### Requirement: Entrada al flujo de arrendamiento desde el detalle del inmueble
El sistema SHALL mostrar un botón "Solicitar arrendamiento" en el detalle público de un inmueble, visible únicamente cuando la sesión activa tiene rol `inquilino`. El sistema SHALL redirigir a la pantalla de login/registro cuando no exista sesión activa, retomando el flujo de arrendamiento tras autenticarse.

#### Scenario: El botón no se muestra a propietarios ni agentes
- **GIVEN** una sesión activa con rol `propietario` o `agente`
- **WHEN** se visualiza el detalle de un inmueble
- **THEN** el botón "Solicitar arrendamiento" no se muestra

#### Scenario: Sin sesión, el clic redirige a autenticación
- **GIVEN** una persona sin sesión activa
- **WHEN** hace clic en "Solicitar arrendamiento"
- **THEN** el sistema la redirige a login/registro, y retoma el flujo de arrendamiento una vez autenticada

#### Scenario: Un inquilino autenticado accede al wizard
- **GIVEN** una sesión activa con rol `inquilino`
- **WHEN** hace clic en "Solicitar arrendamiento"
- **THEN** el sistema navega al wizard de arrendamiento

### Requirement: Wizard de 4 pasos en orden estricto
El sistema SHALL presentar el flujo de arrendamiento como 4 pasos secuenciales (identidad, seguro, firma, arrendamiento activo). El sistema NO SHALL permitir acceder a un paso cuya precondición no está satisfecha según el estado real de los dominios backend.

#### Scenario: No se puede acceder al paso de seguro sin identidad verificada
- **GIVEN** un inquilino sin identidad verificada
- **WHEN** intenta acceder al paso de contratación de seguro
- **THEN** el sistema lo mantiene en el paso de verificación de identidad

#### Scenario: No se puede acceder al paso de firma sin póliza aprobada
- **GIVEN** un inquilino con identidad verificada pero sin póliza de seguro aprobada
- **WHEN** intenta acceder al paso de firma del contrato
- **THEN** el sistema lo mantiene en el paso de contratación de seguro

#### Scenario: El wizard concluye cuando el contrato queda firmado
- **GIVEN** un inquilino que completa exitosamente los 3 primeros pasos
- **WHEN** el contrato queda en estado firmado
- **THEN** el sistema navega a la página "Mi arrendamiento"

### Requirement: Página "Mi arrendamiento" separada del wizard
El sistema SHALL exponer una página "Mi arrendamiento", distinta del wizard, que muestre el arrendamiento activo del inquilino, su historial completo de pagos, y permita iniciar el pago de un `Pago` pendiente.

#### Scenario: El historial de pagos se muestra en "Mi arrendamiento", no en el wizard
- **GIVEN** un inquilino con un arrendamiento activo y pagos previos
- **WHEN** accede a "Mi arrendamiento"
- **THEN** el sistema muestra el historial completo de pagos (pendientes, completados, fallidos), sin que esta pantalla forme parte de los pasos del wizard
