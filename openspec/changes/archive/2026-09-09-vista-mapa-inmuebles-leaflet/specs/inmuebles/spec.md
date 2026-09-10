## MODIFIED Requirements

### Requirement: Creación de publicación de inmueble
El sistema SHALL permitir a un usuario con rol propietario crear una publicación de inmueble completando como mínimo: dirección, barrio, ciudad, tipo de inmueble, área en m², número de habitaciones, número de baños, valor mensual del arriendo y descripción libre. El sistema SHALL rechazar la creación si falta alguno de estos campos o si contienen valores inválidos (ej. valor mensual <= 0, habitaciones o baños negativos).

El sistema SHALL permitir también a un usuario con rol agente crear una publicación de inmueble en nombre de un propietario, indicando explícitamente el `propietario_id` representado. El sistema SHALL rechazar la publicación por parte de un agente si la agencia a la que pertenece no tiene una relación en estado `activa` con ese propietario.

Al crear la publicación, el sistema SHALL intentar geocodificar automáticamente la combinación de `direccion`, `barrio` y `ciudad` contra un proveedor externo (Nominatim/OpenStreetMap) para obtener `latitud`/`longitud`, de forma síncrona dentro del mismo request. Si la geocodificación falla, no responde, o no encuentra un resultado, el sistema NO SHALL bloquear la creación del inmueble: lo crea igualmente con `latitud`/`longitud` en `null`.

#### Scenario: Publicación exitosa con todos los campos requeridos
- **GIVEN** un propietario autenticado
- **WHEN** envía el formulario de publicación con todos los campos requeridos y al menos una foto válidos
- **THEN** el sistema crea el inmueble y responde con sus datos, incluido un identificador único

#### Scenario: Publicación rechazada por campo requerido faltante
- **GIVEN** un propietario autenticado
- **WHEN** envía el formulario de publicación sin el valor mensual del arriendo
- **THEN** el sistema rechaza la solicitud con un error de validación y no crea el inmueble

#### Scenario: Publicación rechazada por valor mensual inválido
- **GIVEN** un propietario autenticado
- **WHEN** envía el formulario de publicación con valor mensual igual a cero o negativo
- **THEN** el sistema rechaza la solicitud con un error de validación y no crea el inmueble

#### Scenario: Agente publica en nombre de un propietario con relación activa
- **GIVEN** un agente autenticado cuya agencia tiene una relación `activa` con un propietario
- **WHEN** publica un inmueble indicando el `propietario_id` de ese propietario
- **THEN** el sistema crea el inmueble asociado a ese propietario, con el `agente_id` del agente que lo publicó

#### Scenario: Agente sin relación activa no puede publicar en nombre de un propietario
- **GIVEN** un agente autenticado cuya agencia NO tiene una relación `activa` con un propietario dado
- **WHEN** intenta publicar un inmueble indicando el `propietario_id` de ese propietario
- **THEN** el sistema rechaza la solicitud sin crear el inmueble

#### Scenario: Publicación exitosa geocodifica la dirección
- **GIVEN** un propietario autenticado que publica un inmueble con una dirección válida y geocodificable
- **WHEN** el sistema completa la creación del inmueble
- **THEN** el inmueble queda guardado con `latitud`/`longitud` correspondientes a esa dirección

#### Scenario: Falla de geocodificación no bloquea la publicación
- **GIVEN** un propietario autenticado publicando un inmueble, y el proveedor de geocodificación no responde o no encuentra la dirección
- **WHEN** el sistema procesa la publicación
- **THEN** el sistema crea el inmueble igualmente, con `latitud`/`longitud` en `null`, y no expone ningún error de geocodificación al usuario

### Requirement: Edición de inmueble publicado
El sistema SHALL permitir editar los datos de un inmueble ya publicado a: (a) el propietario dueño del inmueble, o (b) cualquier agente cuya agencia tenga una relación en estado `activa` con el propietario dueño del inmueble, sin importar si ese agente puntual fue quien lo publicó originalmente. El sistema SHALL rechazar la edición para cualquier otro llamador. El campo `agente_id` del inmueble no SHALL cambiar como resultado de una edición — siempre refleja quién lo publicó originalmente.

Si la edición modifica `direccion`, `barrio` o `ciudad`, el sistema SHALL repetir el intento de geocodificación automática descrito en "Creación de publicación de inmueble" y actualizar `latitud`/`longitud` con el resultado (o dejarlas en `null` si falla). Si la edición no modifica ninguno de esos tres campos, el sistema SHALL conservar sin cambios las coordenadas ya guardadas, sin invocar al proveedor de geocodificación.

#### Scenario: Propietario edita su propio inmueble
- **GIVEN** un propietario autenticado con un inmueble publicado a su nombre
- **WHEN** envía una edición con datos válidos (ej. nuevo valor mensual o descripción)
- **THEN** el sistema actualiza el inmueble con los nuevos datos

#### Scenario: Propietario no puede editar un inmueble ajeno
- **GIVEN** un propietario autenticado
- **WHEN** intenta editar un inmueble publicado por otro propietario
- **THEN** el sistema rechaza la solicitud sin modificar el inmueble

#### Scenario: Un agente de la agencia edita un inmueble publicado por otro agente de la misma agencia
- **GIVEN** un inmueble de un propietario publicado por el Agente A, y la agencia de A tiene relación `activa` con ese propietario
- **WHEN** el Agente B, miembro de la misma agencia, edita ese inmueble
- **THEN** el sistema actualiza el inmueble con los nuevos datos y el campo `agente_id` sigue apuntando al Agente A

#### Scenario: Un agente sin relación activa con el propietario no puede editar
- **GIVEN** un inmueble de un propietario, y la agencia del Agente C NO tiene relación `activa` con ese propietario
- **WHEN** el Agente C intenta editar ese inmueble
- **THEN** el sistema rechaza la solicitud sin modificar el inmueble

#### Scenario: Editar la dirección re-geocodifica el inmueble
- **GIVEN** un inmueble publicado con coordenadas ya guardadas
- **WHEN** su propietario edita la `direccion` a una ubicación distinta
- **THEN** el sistema vuelve a geocodificar y actualiza `latitud`/`longitud` con el resultado de la nueva dirección

#### Scenario: Editar campos sin tocar la ubicación conserva las coordenadas
- **GIVEN** un inmueble publicado con coordenadas ya guardadas
- **WHEN** su propietario edita únicamente el valor mensual o la descripción, sin tocar dirección, barrio ni ciudad
- **THEN** el sistema actualiza los campos editados y conserva `latitud`/`longitud` sin invocar al proveedor de geocodificación

### Requirement: Listado público de inmuebles disponibles
El sistema SHALL permitir listar todos los inmuebles en estado `disponible` sin requerir autenticación. Cada elemento del listado SHALL incluir como mínimo: foto principal, dirección/barrio, ciudad, valor mensual, número de habitaciones, número de baños, y `latitud`/`longitud` (nullable, `null` cuando el inmueble no tiene coordenadas geocodificadas). El sistema NO SHALL incluir inmuebles en estado `oculto` o `no_disponible` en este listado.

#### Scenario: Persona sin sesión ve los inmuebles disponibles
- **GIVEN** varios inmuebles publicados, algunos en estado `disponible` y otros `oculto` o `no_disponible`
- **WHEN** una persona sin sesión activa solicita el listado público
- **THEN** el sistema devuelve únicamente los inmuebles en estado `disponible`, cada uno con foto principal, dirección/barrio, ciudad, valor mensual, habitaciones, baños y sus coordenadas (o `null` si no las tiene)

#### Scenario: Un inmueble deja de listarse al dejar de estar disponible
- **GIVEN** un inmueble listado públicamente en estado `disponible`
- **WHEN** su estado cambia a `oculto` o `no_disponible` (por despublicación o por un arrendamiento activo)
- **THEN** el inmueble deja de aparecer en el listado público, sin ninguna acción adicional sobre este endpoint

#### Scenario: Inmueble sin coordenadas aparece en el listado con coordenadas nulas
- **GIVEN** un inmueble en estado `disponible` cuya geocodificación falló en su momento
- **WHEN** una persona sin sesión activa solicita el listado público
- **THEN** el inmueble aparece en el listado con `latitud` y `longitud` en `null`, junto con el resto de sus datos
