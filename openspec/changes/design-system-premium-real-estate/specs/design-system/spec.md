## ADDED Requirements

### Requirement: Tokens de tipografía, spacing y estilo extendidos
El sistema SHALL exponer, vía `@rentame/design-tokens`, tokens de tipografía (familia Inter para texto, DM Serif Display para títulos grandes; escala Display/H1/H2/H3/Body/Small; pesos 400/500/600/700), spacing (escala de 4px: 4/8/12/16/20/24/32/40/48/64), radios (`--radius-sm` 6px, `--radius-card` 10px, `--radius-lg` 12px), sombras suaves, transiciones, z-index, breakpoints, y un color `--color-warning`. Los componentes NO SHALL usar valores hex ni tamaños de spacing arbitrarios cuando exista un token equivalente.

#### Scenario: Los tokens de tipografía están disponibles como variables CSS
- **GIVEN** cualquier página de `shell` o `inmuebles-app`
- **WHEN** se inspecciona `:root` en el navegador
- **THEN** existen `--font-family-base`, `--font-family-display`, y las variables de tamaño para Display/H1/H2/H3/Body/Small

#### Scenario: Los tokens de spacing siguen la escala de 4px
- **GIVEN** el archivo de tokens de `@rentame/design-tokens`
- **WHEN** se listan los tokens `--space-*`
- **THEN** sus valores son exactamente 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px y 64px, sin valores intermedios arbitrarios

### Requirement: Sistema de botones con variantes y estados
El sistema SHALL exponer un componente `Button` en `@rentame/ui` con variantes Primary (fondo Navy, texto blanco), Secondary (fondo blanco, borde/texto Navy), Ghost, Danger y Premium (acento dorado), cada una con estados default/hover/active/disabled/loading visualmente distinguibles.

#### Scenario: El botón Primary usa Navy de fondo y texto blanco
- **GIVEN** un `Button` variante `primary`
- **WHEN** se renderiza
- **THEN** su color de fondo computado corresponde a `--color-primary` y su color de texto a `--color-surface`

#### Scenario: El estado disabled se distingue visualmente del habilitado
- **GIVEN** un `Button` con `disabled`
- **WHEN** se renderiza
- **THEN** el atributo `disabled` está presente y su estilo visual (opacidad/cursor) difiere del estado habilitado

#### Scenario: El estado loading no permite doble envío
- **GIVEN** un `Button` con `loading`
- **WHEN** se hace clic
- **THEN** el `onClick` no se invoca (mismo comportamiento que `disabled`)

### Requirement: Sistema de badges construido, sin renderizar donde no hay dato real
El sistema SHALL exponer un componente `Badge` en `@rentame/ui` con variantes Verified, Featured, New, Available, Unavailable y Premium, pequeño y discreto. Las variantes `Verified`, `Featured`, `Premium` y `New` NO SHALL renderizarse en ninguna página de la aplicación mientras no exista una funcionalidad de backend real que las respalde (verificación de propietarios, destacados, plan premium). `Available`/`Unavailable` SHALL usarse para reflejar el `estado` real de un inmueble.

#### Scenario: El badge de disponibilidad refleja el estado real del inmueble
- **GIVEN** un inmueble en estado `disponible`
- **WHEN** se muestra en una `PropertyCard`
- **THEN** el badge visible es `Available`, nunca `Verified`/`Featured`/`Premium`/`New`

#### Scenario: Ninguna página renderiza los badges sin dato real
- **GIVEN** el código fuente de `shell` e `inmuebles-app`
- **WHEN** se buscan usos de `<Badge variant="verified"|"featured"|"premium"|"new">`
- **THEN** no existe ningún uso en páginas de producción — solo en el propio componente/sus tests

### Requirement: PropertyCard reutilizable
El sistema SHALL exponer un componente `PropertyCard` en `@rentame/ui` que muestre imagen protagonista, dirección, ubicación (barrio/ciudad), características (habitaciones/baños/área), precio, y un badge de disponibilidad real. El botón de favorito SHALL existir como prop/slot del componente pero NO SHALL renderizarse por defecto ni ser usado por ninguna página hasta que exista una funcionalidad de favoritos real.

#### Scenario: PropertyCard reemplaza las tarjetas ad-hoc del listado público
- **GIVEN** el listado público de inmuebles disponibles
- **WHEN** se renderiza cada inmueble
- **THEN** usa el componente `PropertyCard` de `@rentame/ui`, con la misma información (dirección, ubicación, habitaciones, baños, precio, foto) que mostraba antes

### Requirement: Navegación con identidad Navy
El header/navbar compartido (`AppLayout`) SHALL usar `--color-primary` (Navy) como fondo, con el enlace de la ruta activa resaltado mediante `--color-accent` (dorado), sin cambiar la estructura de rutas ni el comportamiento de sesión ya existente.

#### Scenario: El navbar usa fondo Navy
- **GIVEN** cualquier página de la aplicación
- **WHEN** se inspecciona el header
- **THEN** su color de fondo computado corresponde a `--color-primary`

#### Scenario: El link activo se resalta con el acento dorado
- **GIVEN** la persona está en la ruta "/mis-inmuebles"
- **WHEN** se inspecciona el link "Mis inmuebles" en el navbar
- **THEN** tiene un indicador visual (color/subrayado) usando `--color-accent`, distinto de los links inactivos
