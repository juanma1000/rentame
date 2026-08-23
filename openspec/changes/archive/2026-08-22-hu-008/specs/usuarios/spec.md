## ADDED Requirements

### Requirement: Pantalla de entrada simétrica por rol
El sistema SHALL presentar, a una persona sin sesión activa, tres opciones de registro igualmente visibles: registrarse como propietario, como agente, o como inquilino.

#### Scenario: Persona sin sesión ve las tres opciones
- **GIVEN** una persona que llega a la plataforma sin sesión activa
- **WHEN** accede a la pantalla de entrada
- **THEN** el sistema muestra las tres opciones de registro (propietario, agente, inquilino) sin priorizar visualmente ninguna sobre las otras

### Requirement: Registro como propietario o inquilino
El sistema SHALL permitir registrar una cuenta nueva con rol `propietario` o `inquilino` indicando email, contraseña y nombre. El sistema SHALL otorgar acceso inmediato tras el registro, sin exigir verificación de email.

#### Scenario: Registro exitoso como propietario
- **GIVEN** una persona sin cuenta
- **WHEN** se registra como propietario con email, contraseña y nombre válidos
- **THEN** el sistema crea la cuenta con rol `propietario` y le otorga una sesión activa inmediatamente

#### Scenario: Registro exitoso como inquilino
- **GIVEN** una persona sin cuenta
- **WHEN** se registra como inquilino con email, contraseña y nombre válidos
- **THEN** el sistema crea la cuenta con rol `inquilino` y le otorga una sesión activa inmediatamente

#### Scenario: Registro rechazado por email ya existente
- **GIVEN** una persona sin cuenta
- **WHEN** intenta registrarse con un email que ya tiene una cuenta asociada
- **THEN** el sistema rechaza el registro sin crear una cuenta nueva

### Requirement: Registro como agente requiere resolver el paso de agencia
El sistema SHALL permitir registrar una cuenta nueva con rol `agente` indicando email, contraseña y nombre, pero SHALL considerar el registro incompleto hasta que la persona resuelva el paso de agencia: crear una agencia nueva, o solicitar unirse a una existente. El sistema NO SHALL otorgar una sesión utilizable para gestionar inmuebles/propietarios hasta que ese paso quede resuelto.

#### Scenario: Agente crea una agencia nueva como parte del registro
- **GIVEN** una persona registrándose como agente
- **WHEN** en el mismo flujo elige crear una agencia nueva con razón social y NIT válidos
- **THEN** el sistema crea la cuenta con rol `agente`, crea la agencia, y la persona queda como su primer miembro

#### Scenario: Agente solicita unirse a una agencia existente como parte del registro
- **GIVEN** una persona registrándose como agente, y una agencia existente
- **WHEN** en el mismo flujo busca esa agencia y solicita unirse
- **THEN** el sistema crea la cuenta con rol `agente` y una solicitud de ingreso en estado `pendiente`, sin que la persona sea todavía miembro de ninguna agencia

### Requirement: Rol único y fijo por cuenta
El sistema SHALL fijar el rol elegido durante el registro (`propietario`, `agente` o `inquilino`) de forma permanente. El sistema NO SHALL exponer ningún mecanismo para cambiar el rol de una cuenta existente ni para que una cuenta tenga más de un rol simultáneamente.

#### Scenario: El rol no cambia después del registro
- **GIVEN** una cuenta ya registrada con un rol determinado
- **WHEN** se consulta su rol en cualquier momento posterior
- **THEN** el rol sigue siendo el mismo con el que se registró

### Requirement: Inicio de sesión con email y contraseña
El sistema SHALL permitir a una cuenta ya registrada iniciar sesión con su email y contraseña, y SHALL emitir un JWT (access token) válido para autenticarse en el resto de la plataforma en caso de éxito.

#### Scenario: Login exitoso
- **GIVEN** una cuenta registrada con email y contraseña conocidos
- **WHEN** inicia sesión con esas credenciales
- **THEN** el sistema devuelve un JWT válido con el `sub` (id de usuario) y el rol de esa cuenta

#### Scenario: Login rechazado sin revelar cuál dato falló
- **GIVEN** un intento de login con un email inexistente o con una contraseña incorrecta para un email existente
- **WHEN** se envían esas credenciales
- **THEN** el sistema rechaza el login con un mensaje de error único, sin indicar si el email o la contraseña fue el dato incorrecto

### Requirement: Búsqueda pública sin sesión no se ve afectada
El sistema SHALL mantener el acceso sin sesión a la búsqueda pública de inmuebles disponibles (capacidad `inmuebles`, HU-003) sin exigir ningún requisito de autenticación introducido por esta capacidad.

#### Scenario: Búsqueda pública sigue sin requerir cuenta
- **GIVEN** una persona sin sesión activa
- **WHEN** accede a la búsqueda pública de inmuebles disponibles
- **THEN** el sistema le permite buscar y ver el detalle de inmuebles sin exigirle registrarse ni iniciar sesión
