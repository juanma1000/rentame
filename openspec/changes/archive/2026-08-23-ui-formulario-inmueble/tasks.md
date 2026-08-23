## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/ui-formulario-inmueble` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Estilos compartidos del formulario

- [x] 1.1 `frontend/inmuebles-app/src/styles/{forms.ts,forms.css}` (`cardStyle`, `sectionStyle`, `sectionTitleStyle`, `gridRowStyle`, `inputStyle`, `selectStyle`, `textareaStyle`, `FIELD_CLASS_NAME` para `:focus`) usando `@rentame/design-tokens`

## 2. `FotoDropzone` con preview

- [x] 2.1 qa-expert (Red): tests RTL de `FotoDropzone` — `onFilesSelected` se invoca correctamente vía `fireEvent.change` en el input real y vía `fireEvent.drop` en el contenedor; N miniaturas para N archivos; contador "N/10 fotos"; input sigue siendo `<input type="file" multiple>` accesible por label
- [x] 2.2 frontend-expert (Green): `frontend/inmuebles-app/src/components/FotoDropzone.tsx` (usa `URL.createObjectURL`, revoca URLs anteriores en cleanup de `useEffect`)

## 3. `PublicarInmueblePage`: restyle + integración

- [x] 3.1 qa-expert (Red): tests nuevos — hint de campos faltantes visible/oculto según `isFormReady` (sin `role="alert"`), vista previa de moneda formateada junto a "Valor mensual" sin alterar el valor crudo del input, pantalla de éxito muestra el ícono de check
- [x] 3.2 frontend-expert (Green): reestructurar `PublicarInmueblePage.tsx` — tarjeta contenedora, secciones (Ubicación/Características/Precio y descripción/Fotos), grid de 3 columnas para habitaciones/baños/área, integra `FotoDropzone`, vista previa de moneda, hint de campos faltantes, pantalla de éxito con ícono. Los tests EXISTENTES de este archivo no deben modificarse y deben seguir pasando.

## 4. `EditarInmueblePage`: restyle equivalente

- [x] 4.1 qa-expert (Red): test nuevo de vista previa de moneda (mismo criterio que Publicar); confirma que no hace falta ningún test nuevo de fotos (este formulario no las maneja)
- [x] 4.2 frontend-expert (Green): reestructurar `EditarInmueblePage.tsx` con el mismo `styles/forms.ts`, secciones y grid (sin sección de Fotos ni dropzone), vista previa de moneda, pantalla de éxito con ícono. Los tests EXISTENTES no deben modificarse y deben seguir pasando.

## 5. Verificación de regresión (OBLIGATORIO)

- [x] 5.1 Correr `cd frontend/inmuebles-app && npx jest` y confirmar 0 regresiones sobre TODA la suite existente (`PublicarInmueblePage.test.tsx`, `EditarInmueblePage.test.tsx` y el resto, sin modificarlos) más los tests nuevos en verde
- [x] 5.2 Correr ESLint + `tsc --noEmit`

## 6. Frontend: Testing E2E con Playwright MCP (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 6.1 Asegurar que `docker compose up` esté corriendo (shell, inmuebles-app, backend, postgres) con rebuild de las imágenes tras los cambios
- [x] 6.2 E2E: publicar un inmueble completo usando `setInputFiles` para adjuntar fotos — verificar miniaturas y contador "N/10 fotos" en pantalla
- [x] 6.3 E2E: con el formulario vacío, verificar que el hint de campos faltantes es visible; completar todos los campos y verificar que desaparece y el botón se habilita
- [x] 6.4 E2E: verificar que la vista previa de moneda se actualiza al escribir en "Valor mensual"
- [x] 6.5 E2E: publicar exitosamente y verificar la pantalla de éxito con el ícono (el modo embebido en Mis Inmuebles regresa a la lista, sin cambios de comportamiento; el ícono es del modo standalone, cubierto por tests unitarios)
- [x] 6.6 E2E: editar un inmueble existente y verificar el mismo restyle (secciones, vista previa de moneda) sin fotos
- [x] 6.7 Restaurar el entorno (eliminar cualquier inmueble de prueba creado durante el E2E)
- [x] 6.8 Documentar los escenarios y resultados en `openspec/changes/ui-formulario-inmueble/specs/reports/YYYY-MM-DD-step-6-e2e-playwright.md`

## 7. Documentación (OBLIGATORIO)

- [x] 7.1 Actualizar `docs/architecture/architecture.md` con `FotoDropzone.tsx` y `styles/forms.ts` en el árbol de `inmuebles-app`
