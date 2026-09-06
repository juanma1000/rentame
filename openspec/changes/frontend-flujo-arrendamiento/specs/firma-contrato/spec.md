## ADDED Requirements

### Requirement: Consulta de estado del contrato y arrendamiento activo
El sistema SHALL exponer un endpoint de solo lectura que devuelva el estado del contrato más reciente de la cuenta autenticada (`no_iniciado` si no existe ningún `Contrato`), incluyendo el identificador del `ArrendamientoActivo` cuando el contrato está firmado. El sistema NO SHALL crear ni modificar ningún registro al consultar este estado.

#### Scenario: Cuenta sin contrato generado devuelve no_iniciado
- **GIVEN** una cuenta de inquilino sin ningún `Contrato` registrado
- **WHEN** se consulta su estado de firma
- **THEN** el sistema devuelve `no_iniciado`

#### Scenario: Cuenta con contrato firmado incluye el arrendamiento activo
- **GIVEN** una cuenta de inquilino con un `Contrato` en estado `firmado`
- **WHEN** se consulta su estado de firma
- **THEN** el sistema devuelve `firmado` junto con el identificador del `ArrendamientoActivo` asociado
