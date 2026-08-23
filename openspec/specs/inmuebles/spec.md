# inmuebles

## Purpose

TBD: gestiona la publicación, edición, visibilidad y ciclo de vida de los inmuebles ofrecidos en arriendo por los propietarios en la plataforma.

## Requirements

### Requirement: Creación de publicación de inmueble
El sistema SHALL permitir a un usuario con rol propietario crear una publicación de inmueble completando como mínimo: dirección, barrio, ciudad, tipo de inmueble, área en m², número de habitaciones, número de baños, valor mensual del arriendo y descripción libre. El sistema SHALL rechazar la creación si falta alguno de estos campos o si contienen valores inválidos (ej. valor mensual <= 0, habitaciones o baños negativos).

El sistema SHALL permitir también a un usuario con rol agente crear una publicación de inmueble en nombre de un propietario, indicando explícitamente el `propietario_id` representado. El sistema SHALL rechazar la publicación por parte de un agente si la agencia a la que pertenece no tiene una relación en estado `activa` con ese propietario.

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
El sistema SHALL permitir editar los datos de un inmueble ya publicado a: (a) el propietario dueño del inmueble, o (b) cualquier agente cuya agencia tenga una relación en estado `activa` con el propietario dueño del inmueble, sin importar si ese agente puntual fue quien lo publicó originalmente. El sistema SHALL rechazar la edición para cualquier otro llamador. El campo `agente_id` del inmueble no SHALL cambiar como resultado de una edición — siempre refleja quién lo publicó originalmente.

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

### Requirement: Despublicación temporal del inmueble
El sistema SHALL permitir despublicar (ocultar) y republicar un inmueble a: (a) el propietario dueño del inmueble, o (b) cualquier agente cuya agencia tenga una relación en estado `activa` con el propietario dueño del inmueble. El sistema SHALL rechazar la operación para cualquier otro llamador.

#### Scenario: Propietario oculta un inmueble disponible
- **GIVEN** un propietario autenticado con un inmueble en estado `disponible`
- **WHEN** solicita despublicarlo
- **THEN** el sistema cambia el estado del inmueble a `oculto` y conserva sus datos

#### Scenario: Propietario republica un inmueble oculto
- **GIVEN** un propietario autenticado con un inmueble en estado `oculto`
- **WHEN** solicita republicarlo
- **THEN** el sistema cambia el estado del inmueble a `disponible`

#### Scenario: Un agente de la agencia despublica un inmueble de un propietario vinculado
- **GIVEN** un inmueble en estado `disponible` de un propietario con relación `activa` con la agencia del agente
- **WHEN** el agente solicita despublicarlo
- **THEN** el sistema cambia el estado del inmueble a `oculto`

#### Scenario: Un agente sin relación activa no puede cambiar la disponibilidad
- **GIVEN** un inmueble de un propietario cuya agencia vinculada NO es la del agente que llama
- **WHEN** ese agente intenta despublicarlo o republicarlo
- **THEN** el sistema rechaza la solicitud sin modificar el estado del inmueble

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

### Requirement: Listado de inmuebles gestionados por agencia
El sistema SHALL permitir a un agente consultar el listado de todos los inmuebles de los propietarios cuya relación con la agencia del agente esté en estado `activa`, junto con el estado actual de cada inmueble, sin tener que consultar propietario por propietario.

#### Scenario: Agente consulta los inmuebles que gestiona su agencia
- **GIVEN** un agente cuya agencia tiene relación `activa` con dos propietarios, cada uno con inmuebles publicados
- **WHEN** solicita el listado de inmuebles gestionados
- **THEN** el sistema devuelve los inmuebles de ambos propietarios, cada uno con su estado actual

#### Scenario: Listado excluye inmuebles de propietarios sin relación activa
- **GIVEN** un agente cuya agencia tiene relación `activa` con un propietario y `revocada` con otro
- **WHEN** solicita el listado de inmuebles gestionados
- **THEN** el sistema devuelve únicamente los inmuebles del propietario con relación `activa`

### Requirement: Despublicación en cascada por revocación de agencia
Cuando una relación agencia-propietario pasa a estado revocada (por revocación explícita del propietario o por reemplazo automático al activar una nueva agencia), el sistema SHALL despublicar (cambiar a estado oculto) todos los inmuebles de ese propietario cuyo agente gestor pertenezca a la agencia revocada. Esta operación SHALL reutilizar la operación de cambio de disponibilidad ya existente de la capacidad `inmuebles`, sin modificar su contrato.

#### Scenario: Revocar la agencia despublica los inmuebles que gestionaba
- **GIVEN** un propietario con una relación activa con una agencia, y un inmueble de ese propietario en estado disponible gestionado por un agente de esa agencia
- **WHEN** la relación agencia-propietario pasa a estado revocada
- **THEN** el inmueble pasa a estado oculto sin acción manual del propietario

#### Scenario: Inmuebles publicados directamente por el propietario no se ven afectados
- **GIVEN** un propietario con una relación activa con una agencia, y un inmueble de ese propietario publicado directamente por él mismo (sin agente gestor)
- **WHEN** la relación agencia-propietario pasa a estado revocada
- **THEN** el estado de ese inmueble no cambia

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
