## ADDED Requirements

### Requirement: Alternar entre lista y mapa en el listado público
El sistema SHALL mostrar en el listado público de inmuebles (`/`) un control tipo tab/toggle con las opciones "Lista" y "Mapa". La vista de lista SHALL ser la seleccionada por defecto al cargar la página. El sistema SHALL conservar el mismo conjunto de inmuebles disponibles (`GET /inmuebles/publicos`) en ambas vistas, sin filtros adicionales propios de la vista de mapa.

#### Scenario: La vista de lista es la que se muestra por defecto
- **GIVEN** una persona que abre el listado público de inmuebles por primera vez
- **WHEN** la página termina de cargar
- **THEN** se muestra la vista de lista, con el tab "Mapa" visible pero no seleccionado

#### Scenario: Cambiar a la vista de mapa
- **GIVEN** una persona viendo el listado público en modo lista
- **WHEN** selecciona el tab "Mapa"
- **THEN** el sistema muestra el mapa con los mismos inmuebles disponibles, sin volver a pedir ningún filtro adicional

### Requirement: Marcadores de inmuebles en el mapa
El sistema SHALL renderizar la vista de mapa usando Leaflet con tiles de OpenStreetMap. El sistema SHALL pintar un marcador por cada inmueble disponible que tenga `latitud`/`longitud` no nulas. El sistema NO SHALL pintar ningún marcador para un inmueble sin coordenadas, y esa ausencia NO SHALL producir ningún error visible ni interrumpir la carga del mapa.

#### Scenario: Inmuebles con coordenadas se muestran como marcadores
- **GIVEN** un listado de inmuebles disponibles donde algunos tienen coordenadas y otros no
- **WHEN** una persona abre la vista de mapa
- **THEN** el mapa muestra un marcador por cada inmueble con coordenadas, y ninguno por los que no las tienen

#### Scenario: Ningún inmueble tiene coordenadas
- **GIVEN** un listado de inmuebles disponibles donde ninguno tiene coordenadas
- **WHEN** una persona abre la vista de mapa
- **THEN** el mapa se renderiza vacío (sin marcadores), sin error, y el tab "Mapa" sigue siendo seleccionable

### Requirement: Centrado por defecto del mapa
El sistema SHALL centrar el mapa, al abrirlo, en Medellín o en el centro geográfico de los inmuebles con coordenadas disponibles.

#### Scenario: Mapa se centra con inmuebles disponibles
- **GIVEN** al menos un inmueble disponible con coordenadas
- **WHEN** una persona abre la vista de mapa
- **THEN** el mapa se muestra centrado de forma que los inmuebles con coordenadas son visibles sin necesidad de desplazarse manualmente

### Requirement: Navegación al detalle desde un marcador
El sistema SHALL mostrar, al hacer click/tap sobre un marcador, como mínimo la foto principal y el valor mensual del inmueble correspondiente, junto con una acción para ir a su detalle completo (el mismo detalle público ya expuesto por el listado en modo lista).

#### Scenario: Ver información resumida y navegar al detalle desde un marcador
- **GIVEN** una persona viendo la vista de mapa con al menos un marcador
- **WHEN** hace click/tap sobre ese marcador
- **THEN** el sistema muestra la foto principal y el valor mensual del inmueble, con una acción que lleva a su página de detalle
