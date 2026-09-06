# pagos

## Purpose

TBD - Capacidad para gestionar el pago mensual de renta de un `ArrendamientoActivo`: generación automática del `Pago` pendiente por ciclo, inicio del cobro por parte del inquilino (modelo pull), ejecución del split del monto por la pasarela de pagos entre la prima del seguro de arrendamiento y el giro neto al propietario, registro del resultado como un `Pago` con estado propio, consulta del historial de pagos por arrendamiento, y registro de la necesidad de notificar al propietario ante un pago completado.

## Requirements

### Requirement: Generación automática del pago pendiente por ciclo
El sistema SHALL generar un `Pago` en estado `pendiente` al inicio de cada ciclo mensual de un `ArrendamientoActivo`, mediante un proceso programado. El sistema NO SHALL generar un segundo `Pago` pendiente para el mismo `ArrendamientoActivo` mientras exista uno sin resolver del ciclo actual.

#### Scenario: Se genera un pago pendiente por cada arrendamiento activo
- **GIVEN** un `ArrendamientoActivo` vigente sin `Pago` pendiente para el ciclo actual
- **WHEN** el proceso mensual de generación de pagos se ejecuta
- **THEN** el sistema crea un `Pago` en estado `pendiente` con monto y fecha límite para ese arrendamiento

#### Scenario: El proceso mensual no duplica pagos si se ejecuta más de una vez
- **GIVEN** un `ArrendamientoActivo` que ya tiene un `Pago` pendiente para el ciclo actual
- **WHEN** el proceso mensual de generación de pagos se ejecuta de nuevo
- **THEN** el sistema no crea un segundo `Pago` pendiente para ese arrendamiento y ese ciclo

### Requirement: El inquilino inicia el pago (modelo pull)
El sistema SHALL requerir que el inquilino inicie explícitamente el pago de un `Pago` pendiente. El sistema NO SHALL intentar cobrar automáticamente sin que el inquilino inicie la acción.

#### Scenario: Inquilino inicia el pago de un pago pendiente
- **GIVEN** un `Pago` en estado `pendiente`
- **WHEN** el inquilino inicia su pago
- **THEN** el sistema envía la solicitud de cobro al proveedor de pasarela de pagos

#### Scenario: Un pago ya completado no puede reiniciarse
- **GIVEN** un `Pago` en estado `completado`
- **WHEN** se intenta iniciar su pago nuevamente
- **THEN** el sistema rechaza la operación

### Requirement: Split de pago ejecutado por la pasarela
El sistema SHALL solicitar a la pasarela de pagos que divida el monto cobrado al inquilino entre la retención de la prima mensual del seguro de arrendamiento y el giro neto al propietario del inmueble, dentro de la misma transacción. El sistema NO SHALL recibir el monto completo en una cuenta propia para luego girarlo por su cuenta.

#### Scenario: El pago se divide en la transacción de la pasarela
- **GIVEN** un `Pago` pendiente asociado a un `ArrendamientoActivo` con una `PolizaArrendamiento` aprobada
- **WHEN** el inquilino inicia el pago
- **THEN** el sistema solicita a la pasarela dividir el monto: la prima mensual se retiene y el resto se gira al propietario del inmueble, en la misma operación

### Requirement: Resultado modelado como pago con estado propio
El sistema SHALL registrar el resultado del cobro como un `Pago` con estado (`pendiente`, `completado`, `fallido`), monto, fecha límite, fecha de pago y referencia externa de la pasarela.

#### Scenario: Pago completado exitosamente queda registrado
- **GIVEN** un `Pago` en estado `pendiente` cuyo cobro fue iniciado
- **WHEN** la pasarela reporta que el cobro se completó
- **THEN** el sistema marca el `Pago` como `completado`, con fecha de pago y referencia externa

#### Scenario: Pago fallido queda registrado
- **GIVEN** un `Pago` en estado `pendiente` cuyo cobro fue iniciado
- **WHEN** la pasarela reporta que el cobro falló
- **THEN** el sistema marca el `Pago` como `fallido`, sin fecha de pago

### Requirement: Historial de pagos por arrendamiento
El sistema SHALL permitir consultar el historial completo de `Pago` (pendientes, completados, fallidos) de un `ArrendamientoActivo`.

#### Scenario: El historial incluye pagos en cualquier estado
- **GIVEN** un `ArrendamientoActivo` con pagos en distintos estados a lo largo de varios ciclos
- **WHEN** se consulta su historial de pagos
- **THEN** el sistema devuelve todos los `Pago` de ese arrendamiento, sin filtrar por estado

### Requirement: Notificación a propietario ante pago completado
El sistema SHALL registrar la necesidad de notificar al propietario cuando un `Pago` de su inmueble queda `completado`. La entrega efectiva de esa notificación corresponde a la infraestructura de notificaciones del proyecto, cuando exista.

#### Scenario: Pago completado genera una notificación pendiente para el propietario
- **GIVEN** un `Pago` que pasa a estado `completado` para un inmueble determinado
- **WHEN** el sistema procesa ese resultado
- **THEN** queda registrada la necesidad de notificar al propietario de ese inmueble
