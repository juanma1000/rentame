## ADDED Requirements

### Requirement: Búsqueda pública de agencias
El sistema SHALL permitir buscar agencias por razón social o NIT sin requerir autenticación. El sistema SHALL devolver únicamente los datos públicos de la agencia (razón social, NIT, identificador) necesarios para que un agente pueda elegir a cuál solicitar su ingreso.

#### Scenario: Búsqueda por razón social encuentra la agencia
- **GIVEN** una agencia existente con una razón social conocida
- **WHEN** se busca por un texto que coincide con esa razón social, sin sesión activa
- **THEN** el sistema devuelve esa agencia entre los resultados

#### Scenario: Búsqueda sin coincidencias devuelve lista vacía
- **GIVEN** ninguna agencia cuya razón social o NIT coincida con el texto buscado
- **WHEN** se realiza la búsqueda
- **THEN** el sistema devuelve una lista vacía, no un error
