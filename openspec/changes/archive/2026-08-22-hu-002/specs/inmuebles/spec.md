## MODIFIED Requirements

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

## ADDED Requirements

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
