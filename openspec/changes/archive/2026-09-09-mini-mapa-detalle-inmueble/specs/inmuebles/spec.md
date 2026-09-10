## MODIFIED Requirements

### Requirement: Detalle público de un inmueble disponible
El sistema SHALL permitir consultar el detalle completo (todas las fotos, descripción, dirección, ciudad, tipo, área, habitaciones, baños, valor mensual, `latitud`/`longitud`) de un inmueble en estado `disponible`, sin requerir autenticación. `latitud`/`longitud` SHALL ser nullable — `null` cuando el inmueble no tiene coordenadas geocodificadas. El sistema NO SHALL exponer el detalle de un inmueble que no esté en estado `disponible` a través de este endpoint público.

#### Scenario: Persona sin sesión ve el detalle completo de un inmueble disponible
- **GIVEN** un inmueble en estado `disponible` con varias fotos y coordenadas geocodificadas
- **WHEN** una persona sin sesión activa solicita su detalle por id
- **THEN** el sistema devuelve todos los datos del inmueble, incluidas todas sus fotos ordenadas y sus coordenadas

#### Scenario: El detalle público rechaza un inmueble no disponible
- **GIVEN** un inmueble en estado `oculto` o `no_disponible`
- **WHEN** una persona sin sesión activa solicita su detalle por id a través del endpoint público
- **THEN** el sistema responde como si el inmueble no existiera (404), sin revelar sus datos

#### Scenario: Detalle de un inmueble sin coordenadas geocodificadas
- **GIVEN** un inmueble en estado `disponible` cuya geocodificación falló o no se ha ejecutado
- **WHEN** una persona sin sesión activa solicita su detalle por id
- **THEN** el sistema devuelve el resto de sus datos normalmente, con `latitud` y `longitud` en `null`
