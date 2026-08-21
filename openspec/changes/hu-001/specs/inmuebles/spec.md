## ADDED Requirements

### Requirement: Creación de publicación de inmueble
El sistema SHALL permitir a un usuario con rol propietario crear una publicación de inmueble completando como mínimo: dirección, barrio, ciudad, tipo de inmueble, área en m², número de habitaciones, número de baños, valor mensual del arriendo y descripción libre. El sistema SHALL rechazar la creación si falta alguno de estos campos o si contienen valores inválidos (ej. valor mensual <= 0, habitaciones o baños negativos).

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

### Requirement: Carga de fotos en la publicación
El sistema SHALL requerir un mínimo de 1 foto y SHALL rechazar más de 10 fotos por inmueble. Cada foto se almacena en el object storage configurado y queda asociada al inmueble.

#### Scenario: Publicación con el mínimo de fotos permitido
- **GIVEN** un propietario autenticado completando el formulario de publicación
- **WHEN** adjunta exactamente 1 foto junto con los demás campos requeridos
- **THEN** el sistema crea el inmueble con esa foto asociada

#### Scenario: Publicación rechazada por no adjuntar ninguna foto
- **GIVEN** un propietario autenticado completando el formulario de publicación
- **WHEN** envía el formulario sin adjuntar ninguna foto
- **THEN** el sistema rechaza la solicitud con un error de validación y no crea el inmueble

#### Scenario: Publicación rechazada por exceder el máximo de fotos
- **GIVEN** un propietario autenticado completando el formulario de publicación
- **WHEN** intenta adjuntar 11 fotos o más
- **THEN** el sistema rechaza la solicitud con un error de validación y no crea el inmueble

### Requirement: Estado inicial de la publicación
El sistema SHALL asignar el estado `disponible` a un inmueble inmediatamente después de que su publicación se crea exitosamente, sin pasos de revisión manual adicionales.

#### Scenario: Inmueble disponible inmediatamente tras publicarse
- **GIVEN** un propietario que acaba de publicar un inmueble con datos y fotos válidos
- **WHEN** consulta el detalle del inmueble recién creado
- **THEN** su estado es `disponible`

### Requirement: Edición de inmueble publicado
El sistema SHALL permitir al propietario editar los datos de un inmueble que le pertenece después de publicado. El sistema SHALL rechazar intentos de edición sobre inmuebles que pertenecen a otro propietario.

#### Scenario: Propietario edita su propio inmueble
- **GIVEN** un propietario autenticado con un inmueble publicado a su nombre
- **WHEN** envía una edición con datos válidos (ej. nuevo valor mensual o descripción)
- **THEN** el sistema actualiza el inmueble con los nuevos datos

#### Scenario: Propietario no puede editar un inmueble ajeno
- **GIVEN** un propietario autenticado
- **WHEN** intenta editar un inmueble publicado por otro propietario
- **THEN** el sistema rechaza la solicitud sin modificar el inmueble

### Requirement: Despublicación temporal del inmueble
El sistema SHALL permitir al propietario ocultar (despublicar) un inmueble de su propiedad sin eliminarlo, cambiando su estado a `oculto`. El sistema SHALL permitir volver a publicar (republicar) un inmueble en estado `oculto`, devolviéndolo a `disponible`.

#### Scenario: Propietario oculta un inmueble disponible
- **GIVEN** un propietario autenticado con un inmueble en estado `disponible`
- **WHEN** solicita despublicarlo
- **THEN** el sistema cambia el estado del inmueble a `oculto` y conserva sus datos

#### Scenario: Propietario republica un inmueble oculto
- **GIVEN** un propietario autenticado con un inmueble en estado `oculto`
- **WHEN** solicita republicarlo
- **THEN** el sistema cambia el estado del inmueble a `disponible`

### Requirement: Transición automática a no disponible
El sistema SHALL exponer una operación de aplicación que, al ser invocada con el identificador de un inmueble, cambia su estado a `no_disponible` sin requerir acción manual del propietario. Esta operación es el punto de integración que la capacidad `arrendamiento` invocará cuando un arrendamiento sobre ese inmueble se complete (fuera del alcance de este change: el disparo real desde `arrendamiento` se implementa en el change correspondiente a HU-005).

#### Scenario: Cambio de estado a no disponible sin intervención del propietario
- **GIVEN** un inmueble en estado `disponible` con un identificador válido
- **WHEN** se invoca la operación de cambio a no disponible para ese inmueble
- **THEN** el estado del inmueble pasa a `no_disponible` sin que el propietario haya realizado ninguna acción

#### Scenario: Intento de marcar como no disponible un inmueble inexistente
- **GIVEN** un identificador de inmueble que no existe
- **WHEN** se invoca la operación de cambio a no disponible con ese identificador
- **THEN** el sistema rechaza la operación sin crear ni modificar ningún inmueble

### Requirement: Listado de inmuebles propios
El sistema SHALL permitir al propietario consultar el listado completo de los inmuebles que ha publicado, junto con el estado actual de cada uno (`disponible`, `no_disponible` u `oculto`). El sistema SHALL excluir de ese listado los inmuebles publicados por otros propietarios.

#### Scenario: Propietario consulta su listado de inmuebles
- **GIVEN** un propietario autenticado con varios inmuebles en distintos estados
- **WHEN** solicita su listado de inmuebles
- **THEN** el sistema devuelve únicamente los inmuebles de ese propietario, cada uno con su estado actual

#### Scenario: Listado vacío para un propietario sin inmuebles publicados
- **GIVEN** un propietario autenticado sin inmuebles publicados
- **WHEN** solicita su listado de inmuebles
- **THEN** el sistema devuelve una lista vacía
