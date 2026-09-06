## ADDED Requirements

### Requirement: Cuenta de inquilino expone estado de identidad verificada
El sistema SHALL exponer en la cuenta de un inquilino un atributo `identidad_verificada` (booleano, `False` por defecto), marcado permanentemente en `True` cuando la capacidad `identidad` registra una validación aprobada para esa cuenta. El sistema NO SHALL exponer ningún mecanismo para revertir este atributo de `True` a `False`.

#### Scenario: Cuenta nueva inicia sin identidad verificada
- **GIVEN** una cuenta de inquilino recién registrada
- **WHEN** se consulta su estado de identidad
- **THEN** `identidad_verificada` es `False`

#### Scenario: Identidad verificada se marca tras validación aprobada
- **GIVEN** una cuenta de inquilino sin identidad verificada
- **WHEN** la capacidad `identidad` registra una validación aprobada para esa cuenta
- **THEN** el sistema marca `identidad_verificada = True` de forma permanente
