## ADDED Requirements

### Requirement: Consulta de estado de la póliza de seguro de arrendamiento
El sistema SHALL exponer un endpoint de solo lectura que devuelva el estado de la póliza de seguro de arrendamiento de la cuenta autenticada (`no_iniciado` si no existe ninguna `PolizaArrendamiento`, o el estado de la más reciente, junto con su prima mensual cuando esté aprobada). El sistema NO SHALL crear ni modificar ningún registro al consultar este estado.

#### Scenario: Cuenta sin contratación de seguro devuelve no_iniciado
- **GIVEN** una cuenta de inquilino sin ninguna `PolizaArrendamiento` registrada
- **WHEN** se consulta su estado de seguro
- **THEN** el sistema devuelve `no_iniciado`

#### Scenario: Cuenta con póliza aprobada devuelve su estado y prima
- **GIVEN** una cuenta de inquilino con una `PolizaArrendamiento` en estado `aprobada`
- **WHEN** se consulta su estado de seguro
- **THEN** el sistema devuelve `aprobada` junto con la `prima_mensual`, sin llamar al proveedor externo
