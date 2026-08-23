## Why

La app hoy no tiene una identidad visual ni una navegación consistente: cada página resuelve su propio layout ad-hoc (la landing pública tiene un header inline propio construido en HU-003, las páginas de `inmuebles-app` no tienen ningún header/footer, y algunas páginas usan los tokens de `@rentame/design-tokens` y otras no). No existe un menú persistente — moverse entre "Inicio", "Mis inmuebles" y "Publicar" depende de botones sueltos dentro de cada página. Se pidió explícitamente un pase de diseño usando los tokens ya existentes, con header, footer, menú y botones de navegación consistentes en toda la app.

## What Changes

- Nuevo `AppLayout` en `shell` (header + menú + footer) que envuelve **todas** las rutas (landing pública, login, registro/`EntradaPage`, y el área autenticada `/mis-inmuebles`) — reemplaza el header inline que hoy vive dentro de `BusquedaPublicaShellPage`.
- Menú de navegación persistente y consciente de la sesión: sin sesión → "Inicio" / "Publicar mi inmueble" / "Iniciar sesión"; con sesión → "Inicio" / "Mis inmuebles" / "Cerrar sesión" (mismo comportamiento de sesión ya construido, ahora como menú del layout compartido en vez de lógica embebida en una sola página).
- Footer simple y consistente (marca, año) en todas las páginas.
- Restyle completo con `@rentame/design-tokens` de las páginas que todavía usan estilos inline sin tokens o de forma inconsistente (`LoginPage`, `RegistroPage` donde falte, y todas las páginas de `inmuebles-app`), unificando botones (primario/secundario), tarjetas y formularios.
- La navegación interna de `inmuebles-app` (lista → publicar → editar, manejada por estado local en `PropertyRoutes`/`BusquedaPublicaRoutes`) NO cambia de mecanismo — solo se restylean sus botones ("Volver", "Publicar nuevo inmueble", etc.) con los tokens.

**Fuera de alcance explícito**: no se agregan rutas ni funcionalidades nuevas, no se toca ningún endpoint de backend, no se rediseña el árbol de información de la app — es un pase de estilo y de estructura de layout/navegación sobre lo que ya existe.

## Capabilities

### New Capabilities
- `shell-navegacion`: header, footer y menú persistentes de la aplicación, consistentes en toda la app y conscientes del estado de sesión.

### Modified Capabilities
Ninguna capacidad de dominio (`usuarios`, `agencias`, `inmuebles`) cambia sus requirements — este change es puramente de presentación/frontend.

## Impact

**Frontend / Microfrontends afectados**
- `shell`: nuevo `src/layouts/AppLayout.tsx` (header+footer+menú, envuelve `<Outlet/>`); `App.tsx` reestructura su árbol de rutas para anidar todo bajo este layout; `BusquedaPublicaShellPage.tsx` se simplifica (pierde su header propio, que se absorbe en `AppLayout`); `EntradaPage`/`LoginPage`/`RegistroPage` se restylean donde falte.
- `inmuebles-app`: restyle de `MisInmueblesPage`, `InmueblesGestionadosPage`, `PublicarInmueblePage`, `EditarInmueblePage`, `BusquedaPublicaPage`, `InmuebleDetallePublicoPage` con tokens consistentes (botones primario/secundario compartidos por convención, no por un paquete nuevo).
- No se agregan tokens nuevos al paquete `@rentame/design-tokens` salvo que el restyle revele una necesidad real y consensuada (ej. un tono para estados "neutral"/"warning" ya detectado como faltante en el pase anterior de tokens).

**Backend**: sin cambios.

**Plan de rollback**: cambios puramente de presentación en 2 microfrontends — revertir el código no tiene ninguna dependencia de datos ni de contrato de API.
