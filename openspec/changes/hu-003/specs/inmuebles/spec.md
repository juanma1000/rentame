## ADDED Requirements

### Requirement: Listado público de inmuebles disponibles
El sistema SHALL permitir listar todos los inmuebles en estado `disponible` sin requerir autenticación. Cada elemento del listado SHALL incluir como mínimo: foto principal, dirección/barrio, ciudad, valor mensual, número de habitaciones y número de baños. El sistema NO SHALL incluir inmuebles en estado `oculto` o `no_disponible` en este listado.

#### Scenario: Persona sin sesión ve los inmuebles disponibles
- **GIVEN** varios inmuebles publicados, algunos en estado `disponible` y otros `oculto` o `no_disponible`
- **WHEN** una persona sin sesión activa solicita el listado público
- **THEN** el sistema devuelve únicamente los inmuebles en estado `disponible`, cada uno con foto principal, dirección/barrio, ciudad, valor mensual, habitaciones y baños

#### Scenario: Un inmueble deja de listarse al dejar de estar disponible
- **GIVEN** un inmueble listado públicamente en estado `disponible`
- **WHEN** su estado cambia a `oculto` o `no_disponible` (por despublicación o por un arrendamiento activo)
- **THEN** el inmueble deja de aparecer en el listado público, sin ninguna acción adicional sobre este endpoint

### Requirement: Detalle público de un inmueble disponible
El sistema SHALL permitir consultar el detalle completo (todas las fotos, descripción, dirección, ciudad, tipo, área, habitaciones, baños, valor mensual) de un inmueble en estado `disponible`, sin requerir autenticación. El sistema NO SHALL exponer el detalle de un inmueble que no esté en estado `disponible` a través de este endpoint público.

#### Scenario: Persona sin sesión ve el detalle completo de un inmueble disponible
- **GIVEN** un inmueble en estado `disponible` con varias fotos
- **WHEN** una persona sin sesión activa solicita su detalle por id
- **THEN** el sistema devuelve todos los datos del inmueble, incluidas todas sus fotos ordenadas

#### Scenario: El detalle público rechaza un inmueble no disponible
- **GIVEN** un inmueble en estado `oculto` o `no_disponible`
- **WHEN** una persona sin sesión activa solicita su detalle por id a través del endpoint público
- **THEN** el sistema responde como si el inmueble no existiera (404), sin revelar sus datos
