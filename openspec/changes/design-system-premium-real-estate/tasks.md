## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/design-system-premium-real-estate` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Tokens extendidos

- [x] 1.1 qa-expert (Red): tests de contraste/valores para `--color-warning`, y test que verifica la escala exacta de `--space-*` (4/8/12/16/20/24/32/40/48/64)
- [x] 1.2 frontend-expert (Green): extender `frontend/packages/design-tokens/src/tokens.css` y `tokens.ts` con tipografía (`--font-family-base`, `--font-family-display`, tamaños Display/H1/H2/H3/Body/Small, pesos), spacing (`--space-1`..`--space-10` o nombres equivalentes a 4/8/12/16/20/24/32/40/48/64), radios (`--radius-sm`, `--radius-lg`), sombras (`--shadow-sm`, `--shadow-md`), transiciones (`--transition-base`), z-index (`--z-header`, `--z-modal`), breakpoints (`--breakpoint-sm/md/lg`), y `--color-warning`
- [x] 1.3 frontend-expert: actualizar el `README.md` de `design-tokens` documentando cada token nuevo (mismo formato de tabla ya usado)

## 2. `@rentame/ui`: scaffold + `Button`

- [x] 2.1 crear `frontend/packages/ui/package.json` (mismo patrón que `design-tokens`/`auth`), agregar a `shell`/`inmuebles-app` como `"@rentame/ui": "*"` + `lucide-react`/`@fontsource/inter`/`@fontsource/dm-serif-display`; `npm install` confirmado, symlink `node_modules/@rentame/ui` creado
- [x] 2.2 qa-expert (Red): tests RTL de `Button` — variantes `primary`/`secondary`/`ghost`/`danger`/`premium` con color de fondo/texto correcto; `disabled`/`loading` no disparan `onClick`; `size` `sm`/`md`
- [x] 2.3 frontend-expert (Green): `frontend/packages/ui/src/Button.tsx` + `Button.css` (estados `:hover`/`:active`/`:focus-visible`), usando tokens de `@rentame/design-tokens`

## 3. `@rentame/ui`: `Badge`

- [x] 3.1 qa-expert (Red): tests RTL de `Badge` — las 6 variantes renderizan el texto/color correcto, tamaño pequeño y discreto (verificar `font-size`/`padding` vs el de un `Button`)
- [x] 3.2 frontend-expert (Green): `frontend/packages/ui/src/Badge.tsx`

## 4. `@rentame/ui`: `Input`/`Select`/`Textarea`

- [x] 4.1 qa-expert (Red): tests RTL — altura/tipografía consistente entre los 3, estado `error` (borde/color), `disabled`, foco aplica `--color-primary` (verificar clase/estilo aplicado en foco, no color por defecto del navegador)
- [x] 4.2 frontend-expert (Green): `frontend/packages/ui/src/{Input,Select,Textarea}.tsx` + CSS compartido para el estado `:focus-visible`

## 5. `@rentame/ui`: `PropertyCard`

- [x] 5.1 qa-expert (Red): tests RTL — renderiza foto/dirección/ubicación/características/precio; badge de disponibilidad según `estado` (`disponible`→Available, `oculto`/`no_disponible`→Unavailable); `onClick` se invoca; favorito NO se renderiza por defecto (`showFavorito` ausente/false); slot `acciones` renderiza children cuando se pasa
- [x] 5.2 frontend-expert (Green): `frontend/packages/ui/src/PropertyCard.tsx` (fix aplicado a un regex ambiguo en el test — `/3/` matcheaba también los dígitos de la dirección "20-30"; corregido a match exacto `'3 hab.'`/`'2 baños'`)

## 6. Fuentes e íconos

- [x] 6.1 agregar `lucide-react`, `@fontsource/inter`, `@fontsource/dm-serif-display` a `package.json` de `shell` e `inmuebles-app`; importar las fuentes una vez desde cada `bootstrap.tsx`
- [x] 6.2 Correr `cd frontend/shell && npx jest` y `cd frontend/inmuebles-app && npx jest` — confirmar 0 regresiones tras instalar dependencias nuevas (49 + 118 tests, todos en verde)

## 7. `shell`: `AppLayout` con navbar Navy

- [x] 7.1 qa-expert (Red): tests RTL de `AppLayout` — fondo del header corresponde a `--color-primary`; el link de la ruta activa (via `useLocation`) tiene el indicador de acento dorado; el resto del comportamiento de sesión (tests ya existentes) sigue intacto
- [x] 7.2 frontend-expert (Green): reestructurar `AppLayout.tsx` con `Button`/tokens, navbar Navy, link activo con `--color-accent`, íconos de `lucide-react` donde aplique (ej. logout)

## 8. `shell`: `EntradaPage`/`LoginPage`/`RegistroPage`

- [x] 8.1 frontend-expert: migrar los 3 archivos a `Button`/`Input` de `@rentame/ui` en vez de `styles/buttons.ts` local y estilos inline; aplicar tipografía serif al título principal de `EntradaPage`/`LoginPage`. Los tests EXISTENTES no deben modificarse y deben seguir pasando
- [x] 8.2 Correr `cd frontend/shell && npx jest` — 0 regresiones

## 9. `inmuebles-app`: listado y detalle públicos

- [x] 9.1 frontend-expert: migrar `BusquedaPublicaPage.tsx` para usar `PropertyCard` de `@rentame/ui` en vez del `<li>` ad-hoc; aplicar tipografía serif al `h1` "Inmuebles disponibles"
- [x] 9.2 frontend-expert: migrar `InmuebleDetallePublicoPage.tsx` (título con serif, `Button` para "Volver")
- [x] 9.3 Correr `cd frontend/inmuebles-app && npx jest` — 0 regresiones sobre los tests EXISTENTES de ambos archivos

## 10. `inmuebles-app`: gestión de inmuebles

- [x] 10.1 frontend-expert: migrar `MisInmueblesPage.tsx`/`InmueblesGestionadosPage.tsx` a `PropertyCard` (con slot `acciones` para Despublicar/Republicar/Editar) + `Badge` de disponibilidad, íconos de `lucide-react` en los botones de acción
- [x] 10.2 Correr `cd frontend/inmuebles-app && npx jest` — 0 regresiones sobre los tests EXISTENTES

## 11. `inmuebles-app`: formularios y `FotoDropzone`

- [x] 11.1 frontend-expert: migrar `PublicarInmueblePage.tsx`/`EditarInmueblePage.tsx` a `Input`/`Select`/`Textarea`/`Button` de `@rentame/ui` en vez de `styles/forms.ts`/`styles/buttons.ts` locales; reemplazar el ícono "✓" de texto por `<Check />` de `lucide-react` en la pantalla de éxito
- [x] 11.2 frontend-expert: migrar `FotoDropzone.tsx` — ícono `ImagePlus`/`Upload` de `lucide-react` en vez de solo texto
- [x] 11.3 frontend-expert: retirar `frontend/inmuebles-app/src/styles/{buttons.ts,forms.ts,forms.css}` y `frontend/shell/src/styles/buttons.ts` una vez que ningún archivo los importe (verificar con grep antes de borrar) — `buttons.ts` retirado en ambos microfrontends (sin importadores); `forms.ts`/`forms.css` se mantienen: `cardStyle`/`gridRowStyle`/`sectionStyle`/`sectionTitleStyle` siguen usados por ambas páginas y no hay componente `@rentame/ui` que los reemplace (fuera del alcance de `Input`/`Select`/`Textarea`/`Button`; Tablas/Modals están solo documentados, no construidos, según design.md)
- [x] 11.4 Correr `cd frontend/inmuebles-app && npx jest` — 0 regresiones sobre TODOS los tests EXISTENTES de `PublicarInmueblePage`/`EditarInmueblePage`/`FotoDropzone` (labels, `role="alert"`, contrato de `valorMensual` numérico, etc.)

## 12. Verificación de regresión completa (OBLIGATORIO)

- [x] 12.1 Correr `cd frontend/shell && npx jest` completo — 52/52 passed, 0 regresiones
- [x] 12.2 Correr `cd frontend/inmuebles-app && npx jest` completo — 118/118 passed, 0 regresiones
- [x] 12.3 Correr `cd frontend/packages/design-tokens && npx jest` (48/48) y `cd frontend/packages/ui && npx jest` (47/47)
- [x] 12.4 Correr ESLint + `tsc --noEmit` en `shell`, `inmuebles-app`, `packages/ui`, `packages/design-tokens` — limpio en los 4
- [x] 12.5 `docker compose exec backend pytest --no-cov -q` — 216 passed, sin cambios (este change no lo toca)

## 13. Frontend: Testing E2E con Playwright MCP (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 13.1 Asegurar que `docker compose up` esté corriendo con rebuild de `shell`/`inmuebles-app` tras los cambios
- [x] 13.2 E2E: landing pública — navbar Navy, `PropertyCard` en el grid, tipografía serif en el título, sin errores de consola
- [x] 13.3 E2E: login/registro — navbar Navy con "Iniciar sesión"/"Publicar mi inmueble", formularios con `Input`/`Button` del nuevo sistema
- [x] 13.4 E2E: con sesión activa, el link "Mis inmuebles" se muestra resaltado con acento dorado; `PropertyCard` en la lista de gestión con badge de disponibilidad y botones de acción
- [x] 13.5 E2E: publicar un inmueble completo con el formulario migrado — verificar que sigue funcionando igual (dropzone, preview de moneda, hint) con el nuevo estilo de `Input`/`Button`
- [x] 13.6 Restaurar el entorno (eliminar cualquier inmueble de prueba creado durante el E2E)
- [x] 13.7 Documentar los escenarios y resultados en `openspec/changes/design-system-premium-real-estate/specs/reports/YYYY-MM-DD-step-13-e2e-playwright.md`

## 14. Documentación (OBLIGATORIO)

- [x] 14.1 Actualizar `docs/architecture/architecture.md` con el nuevo paquete `frontend/packages/ui/` y su rol, la extensión de `design-tokens`, y las páginas migradas
- [x] 14.2 Actualizar `docs/frontend-standards.md` si documenta el uso de tokens/componentes, reflejando que `@rentame/ui` es ahora el sistema de componentes de referencia
