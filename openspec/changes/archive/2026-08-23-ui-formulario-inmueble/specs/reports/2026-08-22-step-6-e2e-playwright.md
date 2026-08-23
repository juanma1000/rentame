# Reporte Paso 6 - Testing E2E con Playwright MCP

- Fecha: 2026-08-22
- Cambio: ui-formulario-inmueble
- Agente: Claude Code (Playwright MCP real)

Entorno: `docker compose up` con `inmuebles-app` reconstruido con el rediseño. Baseline pre-test: 4 inmuebles sembrados + 1 propio del usuario (no tocado).

## Escenarios ejecutados

### 6.2 — Publicar con dropzone (drag&drop real vía `setInputFiles`)
Formulario de "Publicar inmueble" muestra secciones (Ubicación/Características/Precio y descripción/Fotos), grid de 3 columnas para área/habitaciones/baños, y el dropzone con el texto "Arrastra tus fotos aquí o hacé clic para seleccionar". Clic en el dropzone abre el selector nativo de archivos; tras adjuntar una foto de prueba, aparece su miniatura y el contador cambia de "0/10 fotos" a "1/10 fotos".

### 6.3 — Hint de campos faltantes
Con el formulario recién abierto (todo vacío), visible: "Completa todos los campos y adjunta al menos 1 foto para publicar." y el botón "Publicar" deshabilitado. Tras completar todos los campos y adjuntar la foto, el hint desaparece y el botón se habilita.

### 6.4 — Vista previa de moneda
Al escribir `1500000` en "Valor mensual", aparece "$ 1.500.000" junto al campo; el valor real del input permanece `1500000` (sin formatear), confirmado también en el formulario de edición del mismo inmueble tras publicarlo.

### 6.5 — Publicación exitosa
Al enviar el formulario completo, el inmueble se publica y aparece en la lista ("Calle 99 # 10-20", estado Disponible) — el flujo embebido en `PropertyRoutes` regresa a la lista automáticamente (comportamiento ya existente vía `onPublicado`, sin cambios); la pantalla de éxito con ícono (`data-testid="icono-exito"`) es la que se muestra en el modo standalone, cubierta por los tests unitarios.

### 6.6 — Editar con el mismo restyle
Abrir "Editar" sobre el inmueble recién creado muestra las mismas secciones (Ubicación/Características/Precio y descripción, sin sección de Fotos) y la misma vista previa de moneda ("$ 1.500.000"), consistente con Publicar.

Sin errores de consola en ningún paso del flujo.

## Restauración del entorno
Se eliminó el inmueble de prueba creado (`Calle 99 # 10-20`, id `7714bfe9-8ead-4e9a-8bd3-55278b9d290b`) y su foto asociada. Conteo final: 4 inmuebles sembrados + 1 propio del usuario (sin tocar) = 5, igual al estado antes de empezar.

## Resultado
- Estado del Paso 6: PASS
- Issues bloqueantes: ninguno
