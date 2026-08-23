## Context

`PublicarInmueblePage.tsx` y `EditarInmueblePage.tsx` (`frontend/inmuebles-app`) comparten la misma estructura de formulario controlado (9 campos + fotos solo en Publicar), con `fieldStyle`/`containerStyle` mínimos (solo `margin`/`flex`, sin tokens) definidos de forma duplicada en cada archivo. El botón de submit ya usa `styles/buttons.ts` (tokens), pero ningún input tiene borde/radio/foco. El contrato de tests (labels vía regex, `valorMensual` como `type="number"` con valor numérico crudo, `<input type="file" multiple>` real, un único `<form>`, mensajes "publicado"/"actualizado", `role="alert"` reservado a las 2 validaciones de fotos) está fijado y no puede romperse — ver reporte de exploración de esta sesión.

## Goals / Non-Goals

**Goals:**
- Restyle completo de ambos formularios con `@rentame/design-tokens`: tarjeta contenedora, secciones, grid, inputs con foco.
- Dropzone con preview de fotos, contador, sin romper el input nativo que los tests manipulan directamente.
- Vista previa de moneda no invasiva (no cambia el tipo/valor del input real).
- Hint de campos faltantes y pantalla de éxito más prominente.

**Non-Goals:**
- No se agregan campos nuevos, no cambia el payload enviado al backend, no se toca `inmuebles.api.ts` más allá de lo estrictamente necesario para thumbnails (URL.createObjectURL, sin llamadas de red nuevas).
- No se introduce una librería de íconos — los íconos (check de éxito, ícono de dropzone) se resuelven con caracteres/SVG inline mínimos, sin dependencia nueva.

## Decisions

**1. El dropzone envuelve el `<input type="file">` real, nunca lo reemplaza**
Nuevo `frontend/inmuebles-app/src/components/FotoDropzone.tsx`: un `<div>` con handlers `onDragOver`/`onDrop` que, al soltar archivos, los asigna al `<input>` real vía `DataTransfer` y dispara su evento `change` de forma nativa (o, más simple y robusto entre navegadores, expone su propio `onFilesSelected(files: File[])` invocado tanto por el `<input onChange>` como por el `onDrop`, delegando el estado a `PublicarInmueblePage`, que sigue siendo la única fuente de verdad de `fotos`). El `<input>` se mantiene en el DOM, asociado a su `<label>` (`htmlFor`), visualmente integrado al dropzone (puede ocupar todo el área o quedar con opacidad 0 sobre ella) — nunca `display:none` en un elemento con el que un test dispara `fireEvent.change` (jsdom sí permite disparar eventos en elementos ocultos, pero se mantiene visible/accesible por consistencia con accesibilidad real).

**2. Miniaturas via `URL.createObjectURL`, limpiadas en `useEffect` cleanup**
Cada `File` seleccionado genera una URL de objeto para el `<img>` de preview; el `useEffect` que las genera revoca las URLs anteriores (`URL.revokeObjectURL`) en su cleanup para no acumular memoria al cambiar la selección.

**3. Vista previa de moneda como elemento adicional, no como el valor del input**
Un `<span>` al lado del input "Valor mensual" (que sigue siendo `type="number"`, valor crudo `1500000`) muestra `new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(valor)` cuando el campo no está vacío. No se toca `handleFieldChange` ni el valor del input — cero riesgo de romper los tests de `toHaveValue`/payload ya fijados.

**4. Hint de campos faltantes es texto plano, nunca `role="alert"`**
Un `<p>` (sin `role`) visible solo cuando `!isFormReady`, calculando qué falta de forma genérica ("Completa todos los campos y adjunta al menos 1 foto para publicar") — no se lista campo por campo (evita mantenimiento fino y posibles colisiones de texto con las labels reales).

**5. Estilos compartidos en `styles/forms.ts` (local a `inmuebles-app`, mismo criterio que `styles/buttons.ts`)**
`sectionStyle`, `sectionTitleStyle`, `gridRowStyle` (3 columnas para habitaciones/baños/área), `inputStyle`/`selectStyle`/`textareaStyle` (borde `--color-border`, radio `--radius-card`, foco `--color-primary`), `cardStyle` (contenedor, `--color-surface`+sombra). Reemplaza `containerStyle`/`fieldStyle` duplicados en ambos archivos de página.

**6. Éxito con ícono simple inline (sin librería)**
Un carácter Unicode "✓" grande dentro de un círculo con `--color-success` de fondo, sin SVG externo ni dependencia nueva — consistente con "sin tokens nuevos salvo necesidad real" del pase anterior.

## Risks / Trade-offs

- **[Riesgo] Simular drag&drop en tests reales de navegador (Playwright) es más frágil que un `fireEvent.change`** → Mitigación: el E2E verifica el flujo por clic (que abre el picker nativo) y por `fireEvent`-equivalente de Playwright (`setInputFiles` sobre el input real, que sigue existiendo y accesible), no intenta simular un `drop` nativo del sistema operativo.
- **[Trade-off] Vista previa de moneda con `Intl.NumberFormat('es-CO', ...)` asume configuración regional colombiana fija** → Aceptado: toda la app ya está en español/COP sin soporte multi-región.

## Testing Strategy por componente

- **`FotoDropzone`**: tests RTL — `onFilesSelected` se invoca con los archivos correctos tanto vía `fireEvent.change` en el input real como vía `fireEvent.drop` en el contenedor; muestra N miniaturas para N archivos; contador "N/10 fotos" se actualiza.
- **`PublicarInmueblePage`**: TODOS los tests existentes deben seguir pasando sin modificarse (contrato ya fijado). Tests nuevos: hint de campos faltantes aparece/desaparece, vista previa de moneda se actualiza y no altera el valor real del input, pantalla de éxito muestra el ícono.
- **`EditarInmueblePage`**: tests existentes sin modificar; test nuevo de vista previa de moneda (mismo criterio que Publicar).
- **E2E**: publicar un inmueble completo verificando drag&drop (vía `setInputFiles`) y preview de miniaturas; hint visible con formulario vacío y desaparece al completarlo; pantalla de éxito con ícono.

## Migration Plan

1. Desplegar `inmuebles-app` con el restyle — cambio de presentación puro, sin migración de datos.
2. **Rollback**: revertir el código no tiene dependencias de datos ni de contrato de API.

## Open Questions

Ninguna — las 8 mejoras ya fueron aceptadas explícitamente por el usuario ("todas").
