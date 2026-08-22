# agencias

## Purpose

TBD: gestiona las agencias inmobiliarias, su membresía de agentes, y las relaciones de representación entre agencias y propietarios.

## Requirements

### Requirement: Creación de agencia
El sistema SHALL permitir a un usuario con rol agente crear una agencia nueva indicando razón social y NIT. El agente que la crea SHALL quedar automáticamente como su primer miembro.

#### Scenario: Agente crea una agencia nueva
- **GIVEN** un usuario autenticado con rol agente que no pertenece a ninguna agencia
- **WHEN** crea una agencia con razón social y NIT válidos
- **THEN** el sistema crea la agencia y registra a ese agente como su primer miembro

### Requirement: Cardinalidad de membresía agente-agencia
El sistema SHALL permitir que un agente pertenezca a exactamente una agencia a la vez. El sistema SHALL rechazar cualquier intento de un agente de unirse a una segunda agencia mientras ya sea miembro de una.

#### Scenario: Agente ya vinculado no puede unirse a otra agencia
- **GIVEN** un agente que ya es miembro de una agencia
- **WHEN** intenta unirse (crear o solicitar ingreso) a una agencia distinta
- **THEN** el sistema rechaza la solicitud sin modificar su membresía actual

### Requirement: Ingreso a una agencia existente requiere aprobación
El sistema SHALL permitir a un agente sin agencia solicitar el ingreso a una agencia existente. La solicitud SHALL quedar en estado pendiente hasta que un agente que ya sea miembro de esa agencia la apruebe. El sistema SHALL rechazar cualquier intento de un agente de quedar vinculado a una agencia sin esa aprobación.

#### Scenario: Solicitud de ingreso queda pendiente hasta aprobación
- **GIVEN** un agente sin agencia y una agencia existente con al menos un miembro
- **WHEN** el agente solicita unirse a esa agencia
- **THEN** la solicitud queda en estado pendiente y el agente todavía no es miembro

#### Scenario: Un miembro existente aprueba el ingreso
- **GIVEN** una solicitud de ingreso pendiente de un agente a una agencia
- **WHEN** un agente que ya es miembro de esa agencia aprueba la solicitud
- **THEN** el agente solicitante queda registrado como miembro de la agencia

#### Scenario: Ingreso sin aprobación es rechazado
- **GIVEN** un agente sin agencia
- **WHEN** intenta quedar vinculado a una agencia existente sin que ningún miembro haya aprobado su ingreso
- **THEN** el sistema rechaza la operación y el agente sigue sin agencia

### Requirement: Sin jerarquía interna de agencia
El sistema SHALL otorgar a todos los agentes miembros de una agencia las mismas capacidades de gestión sobre los propietarios vinculados a esa agencia, sin distinción de roles internos (no existe admin, gerente ni dueño de agencia).

#### Scenario: Cualquier miembro gestiona cualquier propietario de la agencia
- **GIVEN** dos agentes miembros de la misma agencia y un propietario con relación activa con esa agencia
- **WHEN** cualquiera de los dos agentes intenta gestionar ese propietario
- **THEN** el sistema permite la operación a ambos por igual

### Requirement: Salida voluntaria de un agente
El sistema SHALL permitir a un agente abandonar su agencia sin necesidad de aprobación de otro miembro. El sistema SHALL rechazar la salida si el agente es el último miembro de la agencia y esa agencia tiene relaciones en estado activa con propietarios.

#### Scenario: Agente sale de la agencia sin aprobación
- **GIVEN** una agencia con más de un miembro
- **WHEN** uno de los agentes solicita salir
- **THEN** el sistema lo remueve de la agencia sin requerir aprobación de otro miembro

#### Scenario: Se bloquea la salida del último agente con relaciones activas
- **GIVEN** una agencia con un solo miembro y al menos una relación en estado activa con un propietario
- **WHEN** ese agente intenta salir de la agencia
- **THEN** el sistema rechaza la salida y el agente sigue siendo miembro

#### Scenario: Se permite la salida del último agente sin relaciones activas
- **GIVEN** una agencia con un solo miembro y ninguna relación en estado activa con propietarios
- **WHEN** ese agente solicita salir
- **THEN** el sistema lo remueve de la agencia, que queda sin miembros

### Requirement: Relación agencia-propietario iniciada por el propietario
El sistema SHALL permitir a un propietario iniciar una relación con una agencia. La relación SHALL quedar en estado pendiente hasta ser confirmada por un agente miembro de esa agencia, y luego pasar a estado activa.

#### Scenario: Propietario inicia relación con una agencia
- **GIVEN** un propietario autenticado y una agencia existente
- **WHEN** el propietario solicita contratar esa agencia
- **THEN** el sistema crea la relación agencia-propietario en estado pendiente

#### Scenario: Un agente de la agencia confirma la relación
- **GIVEN** una relación agencia-propietario en estado pendiente
- **WHEN** un agente miembro de esa agencia la confirma
- **THEN** la relación pasa a estado activa

### Requirement: Máximo una agencia activa por propietario
El sistema SHALL permitir a un propietario tener como máximo una relación en estado activa con una agencia a la vez. Al activarse una nueva relación agencia-propietario, el sistema SHALL revocar automáticamente cualquier relación previa de ese propietario que estuviera en estado activa.

#### Scenario: Contratar una agencia nueva revoca la anterior
- **GIVEN** un propietario con una relación activa con la Agencia A
- **WHEN** se activa una nueva relación de ese propietario con la Agencia B
- **THEN** la relación con la Agencia A pasa a estado revocada y la relación con la Agencia B queda activa

### Requirement: Revocación de la relación agencia-propietario por el propietario
El sistema SHALL permitir a un propietario revocar su relación activa con una agencia en cualquier momento, sin necesidad de aprobación de la agencia.

#### Scenario: Propietario revoca la relación con su agencia
- **GIVEN** un propietario con una relación activa con una agencia
- **WHEN** el propietario solicita revocarla
- **THEN** la relación pasa a estado revocada sin que la agencia deba aprobarlo

### Requirement: Agente responsable reasignable
El sistema SHALL asociar a cada relación agencia-propietario un agente responsable como punto de contacto. Cualquier agente miembro de la agencia SHALL poder reasignar el agente responsable a otro miembro de la misma agencia. Esta reasignación es de trazabilidad únicamente y no SHALL otorgar ni retirar permisos de gestión.

#### Scenario: Reasignar el agente responsable no cambia quién puede gestionar
- **GIVEN** una relación agencia-propietario activa con un agente responsable asignado
- **WHEN** otro miembro de la misma agencia reasigna el agente responsable a un tercer miembro
- **THEN** el propietario sigue siendo gestionable por cualquier miembro de la agencia, incluido el agente responsable anterior

### Requirement: Listado de propietarios vinculados a la agencia
El sistema SHALL permitir a un agente consultar el listado de propietarios vinculados a su agencia junto con el estado de cada relación y el agente responsable actual.

#### Scenario: Agente consulta la cartera de su agencia
- **GIVEN** un agente miembro de una agencia con varios propietarios vinculados en distintos estados
- **WHEN** solicita el listado de propietarios de su agencia
- **THEN** el sistema devuelve cada propietario con el estado de su relación y el agente responsable actual
