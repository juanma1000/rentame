## ADDED Requirements

### Requirement: Layout persistente en toda la aplicación
El sistema SHALL renderizar un header y un footer consistentes en todas las páginas del `shell` (landing pública, login, registro, y el área autenticada de gestión de inmuebles), usando los tokens de `@rentame/design-tokens` para colores, tipografía y espaciado.

#### Scenario: El header y el footer están presentes en la landing pública
- **GIVEN** una persona sin sesión activa
- **WHEN** visita la landing pública ("/")
- **THEN** ve el header y el footer del layout compartido

#### Scenario: El header y el footer están presentes en el área autenticada
- **GIVEN** una persona con sesión activa
- **WHEN** visita "/mis-inmuebles"
- **THEN** ve el mismo header y footer del layout compartido, sin duplicarse ni faltar

### Requirement: Menú de navegación consciente de la sesión
El sistema SHALL mostrar en el header un menú de navegación cuyas opciones dependen de si hay una sesión activa. Sin sesión, el menú SHALL ofrecer "Inicio", "Publicar mi inmueble" e "Iniciar sesión". Con sesión activa, el menú SHALL ofrecer "Inicio", "Mis inmuebles" y "Cerrar sesión", y NO SHALL mostrar "Iniciar sesión" ni "Publicar mi inmueble" apuntando al flujo de registro.

#### Scenario: Menú sin sesión
- **GIVEN** una persona sin sesión activa
- **WHEN** ve el header en cualquier página
- **THEN** el menú muestra "Inicio", "Publicar mi inmueble" (hacia el flujo de registro) e "Iniciar sesión"

#### Scenario: Menú con sesión activa
- **GIVEN** una persona con sesión activa
- **WHEN** ve el header en cualquier página
- **THEN** el menú muestra "Inicio", "Mis inmuebles" y "Cerrar sesión", y no muestra "Iniciar sesión"

#### Scenario: Cerrar sesión desde el menú regresa al estado sin sesión
- **GIVEN** una persona con sesión activa viendo el menú
- **WHEN** hace clic en "Cerrar sesión"
- **THEN** el sistema termina la sesión y el menú vuelve a mostrar las opciones de "sin sesión", sin necesidad de recargar la página

### Requirement: Navegación interna existente se mantiene, solo restyleada
El sistema SHALL conservar el mecanismo de navegación interna ya existente entre lista/publicar/editar dentro de la gestión de inmuebles (manejado por estado local, sin rutas nuevas), aplicando únicamente estilos consistentes con los tokens a sus botones.

#### Scenario: Los botones de navegación interna usan los tokens de diseño
- **GIVEN** una persona en la vista de "Mis inmuebles"
- **WHEN** ve el botón "Publicar nuevo inmueble" o, dentro del formulario, el botón "Volver"
- **THEN** ambos usan los colores/radios definidos en `@rentame/design-tokens`, consistentes con el resto de la aplicación
