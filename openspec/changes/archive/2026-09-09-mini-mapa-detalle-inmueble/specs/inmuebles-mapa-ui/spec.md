## ADDED Requirements

### Requirement: Mini mapa en el detalle del inmueble
El sistema SHALL mostrar, en la página de detalle público de un inmueble, un mini mapa Leaflet con tiles de OpenStreetMap centrado en las coordenadas de ese inmueble, con un único marcador en su ubicación, cuando el inmueble tenga `latitud`/`longitud` no nulas. El sistema NO SHALL mostrar ninguna sección de mapa cuando el inmueble no tenga coordenadas — su ausencia NO SHALL producir ningún error visible ni afectar el resto de la página de detalle. El mini mapa NO SHALL capturar el scroll del mouse para hacer zoom (`scrollWheelZoom` deshabilitado): el scroll sobre el mini mapa SHALL desplazar la página, igual que sobre cualquier otro contenido de la página de detalle.

#### Scenario: El detalle muestra un mini mapa cuando el inmueble tiene coordenadas
- **GIVEN** un inmueble disponible con `latitud`/`longitud` geocodificadas
- **WHEN** una persona abre su página de detalle
- **THEN** se muestra un mini mapa centrado en esas coordenadas, con un marcador en esa ubicación

#### Scenario: El detalle no muestra mini mapa cuando el inmueble no tiene coordenadas
- **GIVEN** un inmueble disponible sin `latitud`/`longitud` (geocodificación fallida o no ejecutada)
- **WHEN** una persona abre su página de detalle
- **THEN** la página se muestra completa, sin ninguna sección de mapa ni error visible

#### Scenario: El scroll del mouse sobre el mini mapa desplaza la página, no hace zoom
- **GIVEN** una persona viendo el detalle de un inmueble con mini mapa visible
- **WHEN** hace scroll con el mouse mientras el cursor está sobre el mini mapa
- **THEN** la página se desplaza normalmente y el mini mapa no cambia su nivel de zoom
