## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/ui-layout-navegacion-shell` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Shell: `AppLayout` compartido

- [x] 1.1 qa-expert (Red): tests RTL de `AppLayout` — sin sesión (Inicio/Publicar mi inmueble/Iniciar sesión), con sesión (Inicio/Mis inmuebles/Cerrar sesión), clic en "Cerrar sesión" actualiza el menú reactivamente sin recargar, `<Outlet/>` renderiza el contenido hijo
- [x] 1.2 frontend-expert (Green): `frontend/shell/src/layouts/AppLayout.tsx` (header + menú consciente de sesión + footer + `<Outlet/>`)
- [x] 1.3 qa-expert (Red): test de routing actualizado/nuevo que confirme que cada ruta existente sigue montando la página correcta anidada bajo `AppLayout`
- [x] 1.4 frontend-expert (Green): reestructurar `frontend/shell/src/App.tsx` para anidar `/`, `/login`, `/registro/*`, `/publicar` y el árbol de `PrivateLayout` bajo una única `<Route element={<AppLayout/>}>`
- [x] 1.5 frontend-expert: simplificar `frontend/shell/src/pages/BusquedaPublicaShellPage.tsx` — quitar su header propio (ahora vive en `AppLayout`), dejar solo el `Suspense`+lazy-load del remote; actualizar/borrar su test de header si queda obsoleto (documentar el porqué, no borrar tests que sigan siendo válidos)

## 2. Shell: Restyle de páginas sin tokens completos

- [x] 2.1 frontend-expert: `frontend/shell/src/styles/buttons.ts` — `primaryButtonStyle`/`secondaryButtonStyle` con tokens (`var(--color-primary)`, `var(--color-border)`, `var(--radius-card)`)
- [x] 2.2 frontend-expert: aplicar tokens/botones compartidos en `LoginPage.tsx` y `RegistroPage.tsx` donde falte (revisar qué ya se migró en el pase de tokens anterior)
- [x] 2.3 Correr `cd frontend/shell && npx jest` y confirmar 0 regresiones sobre toda la suite existente (los tests no deben requerir cambios si el restyle no toca selectores por rol/texto)

## 3. inmuebles-app: Restyle y botones compartidos

- [x] 3.1 frontend-expert: `frontend/inmuebles-app/src/styles/buttons.ts` (mismo patrón que 2.1, archivo local propio de este microfrontend)
- [x] 3.2 frontend-expert: aplicar los botones compartidos y revisar consistencia de tokens en `MisInmueblesPage.tsx`, `InmueblesGestionadosPage.tsx`, `PublicarInmueblePage.tsx`, `EditarInmueblePage.tsx`, `BusquedaPublicaPage.tsx`, `InmuebleDetallePublicoPage.tsx` (ya usan tokens parcialmente — unificar donde haya inconsistencias, sin agregar tokens nuevos salvo necesidad real documentada inline)
- [x] 3.3 Correr `cd frontend/inmuebles-app && npx jest` y confirmar 0 regresiones sobre toda la suite existente

## 4. Frontend: Testing E2E con Playwright MCP (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 4.1 Asegurar que `docker compose up` esté corriendo (shell, inmuebles-app, backend, postgres) con rebuild de las imágenes tras los cambios
- [x] 4.2 E2E: visitante sin sesión ve header+footer en "/", "/login" y "/publicar"; el menú muestra Inicio/Publicar mi inmueble/Iniciar sesión
- [x] 4.3 E2E: tras loguearse (usuario sembrado), el menú cambia a Inicio/Mis inmuebles/Cerrar sesión sin recargar la página, y el header/footer siguen presentes en "/mis-inmuebles"
- [x] 4.4 E2E: clic en "Cerrar sesión" desde cualquier página vuelve al menú público y a la landing
- [x] 4.5 E2E: navegación interna de inmuebles (lista → Publicar nuevo inmueble → Volver) sigue funcionando, ahora con los botones restyleados
- [x] 4.6 Restaurar el entorno (sin datos de prueba nuevos si el E2E solo lee el seed existente; limpiar cualquier dato creado)
- [x] 4.7 Documentar los escenarios y resultados en `openspec/changes/ui-layout-navegacion/specs/reports/YYYY-MM-DD-step-4-e2e-playwright.md`

## 5. Documentación (OBLIGATORIO)

- [x] 5.1 Actualizar `docs/architecture/architecture.md` con `AppLayout`, la nueva estructura de rutas del `shell`, y los archivos `styles/buttons.ts` de ambos microfrontends
- [x] 5.2 No aplicaba: `docs/frontend-standards.md` no tiene ninguna nota pendiente sobre inconsistencia de tokens (revisado — solo referencia general a `@rentame/design-tokens` en la sección de convenciones); nada que actualizar
