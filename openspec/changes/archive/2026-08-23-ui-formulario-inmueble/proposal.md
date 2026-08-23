## Why

El formulario de publicar/editar inmueble es hoy una lista plana de inputs sin ningún estilo de `@rentame/design-tokens` aplicado a los campos (solo el botón de submit usa tokens) — sin agrupación, sin preview de fotos, con el `<input type="file">` nativo, y sin ninguna pista de qué falta cuando el botón está deshabilitado. El usuario lo señaló explícitamente como "muy básico" y pidió las 8 mejoras visuales propuestas.

## What Changes

- Tarjeta contenedora (`--color-surface`, `--color-border`, `--radius-card`, sombra sutil) para ambos formularios (`PublicarInmueblePage`, `EditarInmueblePage`).
- Agrupación en secciones con subtítulos: Ubicación / Características / Precio y descripción / Fotos (solo Publicar).
- Inputs restyleados con tokens (borde, radio, padding, foco con `--color-primary`).
- Grid responsive de 3 columnas para habitaciones/baños/área.
- Selector de fotos como dropzone con drag&drop, miniaturas de preview y contador "N/10 fotos" — conserva el `<input type="file" multiple>` real y accesible (contrato de tests existente).
- Vista previa de moneda junto a "Valor mensual" (ej. "≈ $1.500.000") sin alterar el valor crudo del input `type="number"` que los tests ya verifican.
- Pantalla de éxito con ícono y mensaje más prominente en ambos formularios.
- Hint de texto (no un nuevo `role="alert"`) explicando qué falta cuando el botón de submit está deshabilitado.

**Fuera de alcance explícito**: no se agregan campos nuevos al formulario, no cambia el contrato de datos enviado al backend, no se toca ningún endpoint.

## Capabilities

### New Capabilities
Ninguna.

### Modified Capabilities
Ninguna capacidad de dominio cambia sus requirements — es un cambio de presentación sobre `inmuebles-app`, mismo criterio que `ui-layout-navegacion`.

## Impact

**Frontend / Microfrontends afectados**
- `inmuebles-app`: `PublicarInmueblePage.tsx`, `EditarInmueblePage.tsx` reestructurados visualmente; nuevo `src/components/FotoDropzone.tsx` (extraído y reusado solo por `PublicarInmueblePage`, ya que `EditarInmueblePage` no maneja fotos); nuevo `src/styles/forms.ts` (estilos de sección/input/grid compartidos por ambos formularios, análogo a `styles/buttons.ts` ya existente).
- `shell`: sin cambios.
- **Restricción dura**: el contrato de tests ya fijado (labels via regex, `valorMensual` como `type="number"` con valor numérico crudo, `<input type="file" multiple>` real accesible por label, un único `<form>` raíz, mensajes "publicado"/"actualizado", `role="alert"` solo para los 2 casos de validación de fotos ya existentes) NO se modifica — todos los tests existentes deben seguir pasando sin tocarlos.

**Backend**: sin cambios.

**Plan de rollback**: cambio puramente de presentación en un microfrontend — revertir el código no tiene dependencias de datos ni de contrato de API.
