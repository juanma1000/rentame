## Context

`@rentame/design-tokens` (paquete workspace, `frontend/packages/design-tokens/`) ya define la paleta de color exacta pedida (Navy/Petrol Blue/Champagne Gold/Background/Surface/Text/Border/Success/Error) y `--radius-card: 10px`, con reglas de contraste documentadas y validadas (`contrast.test.ts`). No existen tokens de tipografía, spacing, sombras, transiciones, z-index ni breakpoints. Los botones/estilos de formulario están duplicados como archivos locales (`styles/buttons.ts`, `styles/forms.ts`) en `shell` e `inmuebles-app` de trabajo previo de esta sesión — funcionan, pero no son un sistema compartido de verdad. `@rentame/auth` ya demuestra que un paquete workspace de solo-TypeScript-fuente (sin build step) es consumible directamente por ambos microfrontends vía Rspack (resuelve symlinks a la ruta real fuera de `node_modules`, evitando el `exclude: /node_modules/` de la regla de `swc-loader`) — mismo patrón que usará `@rentame/ui`.

## Goals / Non-Goals

**Goals:**
- Tokens completos (tipografía, spacing, radios, sombras, transiciones, z-index, breakpoints, `--color-warning`) en `@rentame/design-tokens`.
- Paquete `@rentame/ui` con `Button`, `Badge`, `Input`/`Select`/`Textarea`, `PropertyCard` — componentes React reales, no solo objetos de estilo.
- Migrar las páginas existentes de `shell`/`inmuebles-app` a estos componentes, sin cambiar ninguna ruta, endpoint, ni el contrato de tests ya fijado.
- Navbar (`AppLayout`) con identidad Navy y acento dorado en el link activo.

**Non-Goals:**
- No se agregan rutas, endpoints, ni funcionalidad de dominio nueva (favoritos reales, verificación de propietarios, destacados/premium reales).
- No se construyen `Table`/`Modal`/`Toast` como componentes — solo se documentan sus reglas visuales aquí, para cuando una HU futura los necesite de verdad.
- No se cambia la arquitectura de Module Federation ni el mecanismo de routing existente.

## Decisions

**1. `@rentame/ui` es un paquete workspace de solo TypeScript fuente, sin build step — mismo patrón que `@rentame/auth`**
`frontend/packages/ui/` con `package.json` (`main`/`types` apuntando a `src/index.ts`, igual que `design-tokens`/`auth`), consumido como `@rentame/ui` desde `shell` e `inmuebles-app` (agregado a sus `package.json` como `"@rentame/ui": "*"` y a los `workspaces` de `frontend/frontend/package.json` si no está ya cubierto por `packages/*`). No requiere cambios en `rspack.config.ts` de ninguna app — Rspack ya resuelve paquetes workspace por symlink a su ruta real, fuera de `node_modules`, transpilándolos con la misma regla `swc-loader` que el resto del código fuente.

**2. Componentes con props explícitas, sin `className` libre desde el caller**
`Button`, `Badge`, `Input`, `PropertyCard` reciben props tipadas (`variant`, `size`, `disabled`, `loading`, etc.) — no aceptan `style`/`className` arbitrario desde quien los usa, para que el sistema sea realmente consistente (si una página necesita algo que el componente no soporta, se agrega una prop nueva al componente, no un override por fuera). Excepción: `PropertyCard` acepta un `onClick` (para navegación, ya que ninguno de los dos microfrontends asume react-router dentro de componentes compartidos, mismo criterio que `BusquedaPublicaPage`/`PropertyRoutes`).

**3. `Button`: variantes y estados**
`variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'premium'`, `size?: 'sm' | 'md'`, `loading?: boolean`, `disabled?: boolean`. Estados vía CSS real (no solo objetos inline) — se agrega un `button.css` (mismo patrón que `forms.css` en `inmuebles-app`) para `:hover`/`:active`/`:focus-visible`, ya que esos pseudo-estados no son expresables con `style={}` de React. `loading` deshabilita el `onClick` y muestra un spinner mínimo (CSS puro, sin librería).

**4. `Badge`: construido completo, uso restringido por convención + lint**
Las 6 variantes (`verified`, `featured`, `new`, `available`, `unavailable`, `premium`) existen y tienen tests, pero solo `available`/`unavailable` se usan en código de producción (reflejan el `estado` real de `Inmueble`). Se documenta en el `README` de `@rentame/ui` (no hay forma de "prohibir" en tiempo de compilación el uso de una variante sin sobre-ingeniería) que las demás quedan reservadas para cuando exista backend real — el requirement de specs verifica esto por búsqueda de código, no por un mecanismo en runtime.

**5. `PropertyCard`: reemplaza las tarjetas ad-hoc, favorito como slot no usado**
Props: `{ direccion, barrio, ciudad, habitaciones, banos, valorMensual, fotoUrl, estado, onClick? }`. El ícono de favorito existe como sub-componente interno opcional (`showFavorito?: boolean`, default `false`) — ningún caller lo activa todavía. Reemplaza el `<li>` de `BusquedaPublicaPage` y las filas de `MisInmueblesPage`/`InmueblesGestionadosPage` (estas últimas necesitan además los botones de acción — `PropertyCard` acepta un slot `acciones?: ReactNode` para "Despublicar"/"Editar", ya que esos botones no existen en el listado público).

**6. Íconos: `lucide-react`, uno por concepto, nunca emoji**
Reemplaza el "✓" de texto plano usado hoy en la pantalla de éxito de `PublicarInmueblePage`/`EditarInmueblePage` por `<Check />` de `lucide-react`; agrega íconos a los botones de "Despublicar" (`EyeOff`), "Editar" (`Pencil`), dropzone de fotos (`ImagePlus`), etc. `lucide-react` se agrega como dependencia de ambos microfrontends (paquete de íconos SVG puros, sin runtime pesado, tree-shakeable).

**7. Fuentes: `@fontsource/inter` y `@fontsource/dm-serif-display`, autohospedadas**
Se importan una vez desde el entrypoint de cada microfrontend (`bootstrap.tsx`), igual que ya se hace con `@rentame/design-tokens/src/tokens.css` — sin `<link>` externo a Google Fonts, consistente con "sin llamadas de red externas evitables" del resto del proyecto.

**8. `AppLayout`: navbar Navy, link activo con acento dorado**
Fondo `--color-primary`, texto `--color-surface`/`--color-accent`. El link activo se determina con `useLocation()` de `react-router` (ya usado en el proyecto) comparando `pathname`; se resalta con `border-bottom: 2px solid var(--color-accent)` (no fondo dorado sólido — la regla de contraste del propio README de tokens prohíbe dorado como fill con texto blanco).

**9. Migración incremental por archivo, tests existentes intactos**
Cada página migra sus estilos inline/objetos locales a los componentes de `@rentame/ui` de a una, sin modificar ningún test existente — los tests ya fijan contrato por rol/label/texto, no por estructura de estilo, así que deberían sobrevivir la migración (ya validado repetidas veces en esta sesión con `styles/buttons.ts`/`styles/forms.ts`). Al terminar, se retiran `styles/buttons.ts` (`shell`, `inmuebles-app`) y `styles/forms.ts` (`inmuebles-app`) — sin dejar código duplicado muerto.

## Reglas visuales para Tablas/Modals/Toasts (documentadas, no implementadas)

Para cuando una HU futura los necesite, sin construir nada ahora:
- **Tablas**: header con fondo `--color-background`, texto `--color-text-secondary` en mayúsculas pequeñas; filas con `border-bottom: 1px solid var(--color-border)`; hover con `--color-background` sutil; estados vía `Badge`, nunca color de fondo de fila completo.
- **Modals/Drawers**: `--color-surface`, `--radius-lg` (12px), sombra suave (mismo `boxShadow` ya usado en `cardStyle` de `inmuebles-app`), header con título + botón de cerrar, footer con acciones alineadas a la derecha (`Button` primary + secondary).
- **Toasts**: variantes success/error/warning/info con el color correspondiente solo en un borde izquierdo de 3-4px + ícono, fondo `--color-surface` — nunca fondo de color sólido saturado.

## Risks / Trade-offs

- **[Riesgo] Migrar 10+ páginas a un paquete nuevo en un solo change es una superficie grande** → Mitigación: migración archivo por archivo con TDD (tests existentes deben seguir en verde en cada paso), decidido explícitamente como "un solo change grande" por el usuario tras sopesar la alternativa de fases.
- **[Trade-off] `Button`/`Input`/`Badge` sin `className` libre** → Aceptado: fuerza a que cualquier necesidad de estilo nueva pase por el componente (más consistente a largo plazo), a costa de tener que extender el componente si una página necesita algo genuinamente distinto.
- **[Riesgo] `lucide-react`/`@fontsource` aumentan el bundle de ambos microfrontends** → Mitigación: `lucide-react` es tree-shakeable (solo se importan los íconos usados); las fuentes autohospedadas solo cargan los pesos/estilos realmente usados (400/500/600/700 de Inter, un solo peso de DM Serif Display).

## Migration Plan

1. Desplegar `@rentame/design-tokens` extendido y `@rentame/ui` nuevo (sin consumidores todavía — no rompe nada).
2. Migrar `shell` (`AppLayout`, `EntradaPage`, `LoginPage`, `RegistroPage`) y desplegar.
3. Migrar `inmuebles-app` (todas sus páginas + `FotoDropzone`) y desplegar, retirando `styles/buttons.ts`/`styles/forms.ts` locales.
4. **Rollback**: revertir cualquiera de los 2 microfrontends es independiente del otro (no comparten build) — sin dependencias de datos ni de contrato de API.

## Testing Strategy por componente

- **Tokens** (`@rentame/design-tokens`): tests existentes de contraste (`contrast.test.ts`) se extienden para `--color-warning`; test nuevo que verifica la escala de spacing (valores exactos de la escala de 4px).
- **`Button`**: tests RTL por variante (color de fondo/texto computado), `disabled`/`loading` no disparan `onClick`.
- **`Badge`**: tests RTL de las 6 variantes renderizando el texto/ícono correcto; test de "grep" a nivel de repo (o revisión manual documentada) confirmando que `verified`/`featured`/`premium`/`new` no se usan en páginas de producción.
- **`Input`/`Select`/`Textarea`**: tests RTL de estado `error` (borde/color), `disabled`, y que el foco aplica el estilo de `--color-primary`.
- **`PropertyCard`**: tests RTL — renderiza todos los datos, badge de disponibilidad correcto según `estado`, `onClick` se invoca, favorito no se renderiza por defecto.
- **Páginas migradas**: NINGÚN test existente se modifica; deben seguir pasando tal cual tras la migración (esa es la señal de que el restyle no rompió el contrato).
- **E2E**: recorrido visual completo (landing, login, publicar, mis inmuebles) confirmando navbar Navy, PropertyCard en el listado, botones con las variantes correctas, sin errores de consola.

## Open Questions

Ninguna — las 7 decisiones de alcance/arquitectura se cerraron en `/opsx:explore`.
