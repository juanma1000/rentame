## ADDED Requirements

### Requirement: Consulta de estado de validación de identidad
El sistema SHALL exponer un endpoint de solo lectura que devuelva el estado de validación de identidad de la cuenta autenticada (`no_iniciado` si no existe ninguna `ValidacionIdentidad`, o el estado de la más reciente). El sistema NO SHALL crear ni modificar ningún registro al consultar este estado.

#### Scenario: Cuenta sin intento de validación devuelve no_iniciado
- **GIVEN** una cuenta de inquilino sin ninguna `ValidacionIdentidad` registrada
- **WHEN** se consulta su estado de identidad
- **THEN** el sistema devuelve `no_iniciado`

#### Scenario: Cuenta con validación aprobada devuelve su estado real
- **GIVEN** una cuenta de inquilino con una `ValidacionIdentidad` en estado `aprobado`
- **WHEN** se consulta su estado de identidad
- **THEN** el sistema devuelve `aprobado`, sin llamar al proveedor externo
