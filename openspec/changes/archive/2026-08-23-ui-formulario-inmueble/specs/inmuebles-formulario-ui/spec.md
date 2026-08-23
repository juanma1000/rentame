## ADDED Requirements

### Requirement: Selector de fotos con preview
El formulario de publicar inmueble SHALL permitir seleccionar fotos mediante arrastrar-y-soltar o clic, mostrando una miniatura por cada foto seleccionada y un contador de cuántas fotos se han adjuntado sobre el máximo permitido. El campo SHALL seguir siendo un `<input type="file" multiple>` real y accesible por su etiqueta.

#### Scenario: Se muestran miniaturas al seleccionar fotos
- **GIVEN** el formulario de publicar inmueble sin fotos adjuntas
- **WHEN** la persona selecciona 3 fotos
- **THEN** el sistema muestra 3 miniaturas y un contador "3/10 fotos"

#### Scenario: El contador refleja el máximo permitido
- **GIVEN** el formulario de publicar inmueble
- **WHEN** la persona no ha seleccionado ninguna foto
- **THEN** el contador muestra "0/10 fotos"

### Requirement: Indicación de campos faltantes cuando el botón está deshabilitado
El formulario SHALL mostrar un texto explicativo (no un `role="alert"`, que queda reservado a los errores de validación de fotos ya existentes) indicando que hay campos pendientes cuando el botón de envío está deshabilitado por formulario incompleto.

#### Scenario: Se muestra el hint con el formulario incompleto
- **GIVEN** el formulario de publicar inmueble con campos vacíos
- **WHEN** la persona no ha completado todos los campos requeridos ni adjuntado una foto
- **THEN** el sistema muestra un texto indicando que faltan campos por completar, sin usar `role="alert"`

#### Scenario: El hint desaparece cuando el formulario está completo
- **GIVEN** el formulario de publicar inmueble
- **WHEN** la persona completa todos los campos requeridos y adjunta al menos 1 foto
- **THEN** el texto de campos faltantes ya no se muestra y el botón de envío se habilita

### Requirement: Vista previa de moneda en el valor mensual
El formulario SHALL mostrar una vista previa formateada (con separador de miles) del valor mensual ingresado, sin alterar el valor numérico crudo que se envía al backend.

#### Scenario: La vista previa se actualiza mientras se escribe
- **GIVEN** el campo "Valor mensual" vacío
- **WHEN** la persona escribe `1500000`
- **THEN** el sistema muestra una vista previa formateada como "$1.500.000" junto al campo, y el valor enviado al backend sigue siendo `1500000` (número)
