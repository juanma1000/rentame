## Why

La interfaz actual usa estilos inline dispersos y duplicados por microfrontend, sin tipografía, spacing, sombras ni componentes reutilizables — solo una paleta de color parcial (`@rentame/design-tokens`, ya alineada con la dirección "Premium Real Estate" deseada, pero sin nada más). El usuario pidió transformar visualmente la app en una plataforma inmobiliaria premium de alquiler de larga estancia, sin tocar arquitectura, lógica de negocio, rutas, APIs ni flujos funcionales — explorado y cerrado en `/opsx:explore` (7 decisiones).

## What Changes

- Extender `@rentame/design-tokens`: tokens de tipografía (Inter + DM Serif Display, escala Display/H1/H2/H3/Body/Small, pesos 400/500/600/700), spacing (escala de 4px: 4/8/12/16/20/24/32/40/48/64), radios (`--radius-sm` 6px, `--radius-card` 10px ya existente, `--radius-lg` 12px), sombras suaves, transiciones, z-index, breakpoints, y `--color-warning` (#B7791F) nuevo.
- Nuevo paquete `@rentame/ui` (componentes React compartidos): `Button` (Primary/Secondary/Ghost/Danger/Premium, con estados default/hover/active/disabled/loading), `Badge` (Verified/Featured/New/Available/Unavailable/Premium — `Verified`/`Featured`/`Premium`/`New` se construyen pero no se renderizan en ninguna página todavía, sin dominio real detrás), `Input`/`Select`/`Textarea` (altura/tipografía/border/focus/error/disabled consistentes), `PropertyCard` (imagen protagonista, badge de disponibilidad real, favorito visual construido pero no renderizado, dirección, ubicación, características, precio).
- `lucide-react` (íconos) y `@fontsource` (Inter, DM Serif Display) como dependencias nuevas de ambos microfrontends.
- Aplicar el sistema a las páginas/componentes existentes: `AppLayout` (navbar Navy, link activo con acento dorado), `EntradaPage`/`LoginPage`/`RegistroPage`, `BusquedaPublicaPage`/`InmuebleDetallePublicoPage` (usan `PropertyCard`), `MisInmueblesPage`/`InmueblesGestionadosPage` (usan `PropertyCard` + `Badge` de estado), `PublicarInmueblePage`/`EditarInmueblePage` (usan `Input`/`Select`/`Textarea`/`Button` del nuevo paquete en vez de `styles/forms.ts`/`styles/buttons.ts` locales), `FotoDropzone`.

**Fuera de alcance explícito** (no inventar): tablas, modals/drawers y toasts — se documentan las reglas visuales en `design.md` pero no se construyen componentes sin ningún caller real hoy. Favoritos y verificación de propietarios como funcionalidad real (solo el componente visual, sin persistencia ni backend).

**Restricción dura**: ningún cambio de arquitectura, lógica de negocio, ruta, endpoint o comportamiento funcional. Todo el contrato de tests existente (labels, roles, mensajes, `role="alert"` en fotos, forma de los datos enviados al backend) se mantiene intacto.

## Capabilities

### New Capabilities
- `design-system`: tokens extendidos (tipografía, spacing, sombras, transiciones, z-index, breakpoints, warning) y el paquete `@rentame/ui` (Button, Badge, Input, PropertyCard) como sistema visual reutilizable de toda la aplicación.

### Modified Capabilities
Ninguna capacidad de dominio ni de UI ya existente (`shell-navegacion`, `inmuebles-formulario-ui`) cambia sus requirements — es un cambio puramente de presentación sobre componentes ya construidos, mismo criterio que `ui-layout-navegacion`/`ui-formulario-inmueble`.

## Impact

**Frontend / Microfrontends afectados**
- Nuevo `frontend/packages/ui/` (paquete compartido, workspace de `frontend/frontend/package.json`), consumido por `shell` e `inmuebles-app`.
- `frontend/packages/design-tokens/`: extendido (no reescrito) con los tokens nuevos.
- `shell`: `AppLayout.tsx` (navbar Navy), `EntradaPage`/`LoginPage`/`RegistroPage` migran a `@rentame/ui`.
- `inmuebles-app`: `BusquedaPublicaPage`/`InmuebleDetallePublicoPage`/`MisInmueblesPage`/`InmueblesGestionadosPage`/`PublicarInmueblePage`/`EditarInmueblePage`/`FotoDropzone` migran a `@rentame/ui`; `styles/buttons.ts`/`styles/forms.ts` locales se retiran una vez migrados (sin dejar código muerto).
- `frontend/shell/src/styles/buttons.ts` (local a shell) también se retira tras la migración.

**Backend**: sin cambios.

**Plan de rollback**: cambio puramente de presentación en 2 microfrontends más un paquete nuevo — revertir el código no tiene dependencias de datos ni de contrato de API. El paquete `@rentame/ui` puede quedar sin consumidores (huérfano) si se revierte solo la aplicación a las páginas, sin romper nada.
