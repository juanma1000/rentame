# @rentame/design-tokens

Tokens de color y estilo base compartidos por los módulos federados del frontend (`shell`, `inmuebles-app`, y futuros remotes como el de agencias de HU-007).

## Uso

CSS (variables globales):

```css
@import '@rentame/design-tokens/src/tokens.css';

.card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
}
```

TypeScript:

```ts
import { colors, radius } from '@rentame/design-tokens';
```

## Tokens de color

| Token | Variable CSS | Constante TS | Valor | Uso |
| --- | --- | --- | --- | --- |
| Primary | `--color-primary` | `colors.primary` | `#0F172A` | Navy — color de marca principal, fondos de botones primarios, texto sobre acentos claros |
| Primary 2 | `--color-primary-2` | `colors.primary2` | `#1E3A5F` | Azul petróleo — variante secundaria de marca |
| Accent | `--color-accent` | `colors.accent` | `#C8A96B` | Dorado champagne — **solo como acento puntual**: bordes, íconos, badges de "verificado"/"destacado"/"premium", hover de elementos premium. **No usar como fondo sólido con texto blanco** (contraste 2.25:1, falla el mínimo de 3:1). Si se necesita un fill sólido, usar texto `--color-primary` encima (contraste 7.94:1) |
| Background | `--color-background` | `colors.background` | `#F7F4ED` | Beige — fondo de página |
| Surface | `--color-surface` | `colors.surface` | `#FFFFFF` | Blanco — fondo de tarjetas y superficies de contenido |
| Text | `--color-text` | `colors.text` | `#111827` | Texto principal |
| Secondary text | `--color-text-secondary` | `colors.textSecondary` | `#64748B` | **Solo sobre `--color-surface`** (contraste 4.76:1). **No usar directo sobre `--color-background`** (contraste 4.33:1, no alcanza el mínimo AA de 4.5:1 para texto normal) |
| Border | `--color-border` | `colors.border` | `#E5E1D8` | Divisores dentro de una superficie blanca. Sobre `--color-background` el contraste es de solo 1.19:1 — no confiar en él para separar una tarjeta del fondo; usar `--color-surface` + sombra para eso |
| Success | `--color-success` | `colors.success` | `#3F7D58` | Estados positivos (ej. relación `activa`) |
| Error | `--color-error` | `colors.error` | `#B94A48` | Estados de error/alerta |
| Warning | `--color-warning` | `colors.warning` | `#B7791F` | Estados de advertencia. Contraste con `--color-primary` como texto/gráfico encima ≥3:1 (AA elementos grandes/gráficos) |

## Tokens de estilo

| Token | Variable CSS | Constante TS | Valor | Uso |
| --- | --- | --- | --- | --- |
| Radio de tarjeta | `--radius-card` | `radius.card` | `10px` | Esquinas de tarjetas y superficies — sobrio, no redondeado tipo startup (rango aceptado 10–12px) |
| Radio pequeño | `--radius-sm` | `radius.sm` | `6px` | Controles pequeños: inputs, badges, chips |
| Radio grande | `--radius-lg` | `radius.lg` | `12px` | Contenedores grandes, modales, paneles |

## Tokens de tipografía

| Token | Variable CSS | Constante TS | Valor | Uso |
| --- | --- | --- | --- | --- |
| Familia base | `--font-family-base` | `typography.fontFamilyBase` | `'Inter', sans-serif` | Tipografía de texto general de la UI |
| Familia display | `--font-family-display` | `typography.fontFamilyDisplay` | `'DM Serif Display', serif` | Titulares editoriales / hero, look premium inmobiliario |
| Tamaño display | `--font-size-display` | `typography.fontSizeDisplay` | `48px` | Titular hero de página |
| Tamaño H1 | `--font-size-h1` | `typography.fontSizeH1` | `32px` | Título principal de sección/página |
| Tamaño H2 | `--font-size-h2` | `typography.fontSizeH2` | `24px` | Subtítulo de sección |
| Tamaño H3 | `--font-size-h3` | `typography.fontSizeH3` | `20px` | Encabezado de bloque/tarjeta |
| Tamaño body | `--font-size-body` | `typography.fontSizeBody` | `16px` | Texto de párrafo/UI estándar |
| Tamaño small | `--font-size-small` | `typography.fontSizeSmall` | `13px` | Texto auxiliar, metadatos, ayudas |
| Peso regular | `--font-weight-regular` | `typography.fontWeightRegular` | `400` | Texto de párrafo |
| Peso medium | `--font-weight-medium` | `typography.fontWeightMedium` | `500` | Énfasis leve, labels |
| Peso semibold | `--font-weight-semibold` | `typography.fontWeightSemibold` | `600` | Subtítulos, botones |
| Peso bold | `--font-weight-bold` | `typography.fontWeightBold` | `700` | Títulos, énfasis fuerte |

## Tokens de espaciado (escala 4px)

| Token | Variable CSS | Constante TS | Valor |
| --- | --- | --- | --- |
| Space 1 | `--space-1` | `spacing[1]` | `4px` |
| Space 2 | `--space-2` | `spacing[2]` | `8px` |
| Space 3 | `--space-3` | `spacing[3]` | `12px` |
| Space 4 | `--space-4` | `spacing[4]` | `16px` |
| Space 5 | `--space-5` | `spacing[5]` | `20px` |
| Space 6 | `--space-6` | `spacing[6]` | `24px` |
| Space 8 | `--space-8` | `spacing[8]` | `32px` |
| Space 10 | `--space-10` | `spacing[10]` | `40px` |
| Space 12 | `--space-12` | `spacing[12]` | `48px` |
| Space 16 | `--space-16` | `spacing[16]` | `64px` |

## Tokens de sombra, transición y z-index

| Token | Variable CSS | Constante TS | Valor | Uso |
| --- | --- | --- | --- | --- |
| Sombra pequeña | `--shadow-sm` | `shadows.sm` | `0 1px 2px rgba(0, 0, 0, 0.05)` | Elevación sutil (hover de tarjetas, inputs) |
| Sombra media | `--shadow-md` | `shadows.md` | `0 1px 3px rgba(0, 0, 0, 0.08)` | Elevación estándar de tarjetas/paneles (mismo valor usado en `inmuebles-app/src/styles/forms.ts`) |
| Transición base | `--transition-base` | `transitions.base` | `150ms ease` | Transiciones de hover/foco/estado en controles |
| Z-index header | `--z-header` | `zIndex.header` | `100` | Header/nav fijo |
| Z-index modal | `--z-modal` | `zIndex.modal` | `1000` | Modales/overlays, siempre por encima del header |

## Breakpoints

| Token | Variable CSS | Constante TS | Valor | Uso |
| --- | --- | --- | --- | --- |
| Small | `--breakpoint-sm` | `breakpoints.sm` | `640px` | Móvil grande / tablet chica |
| Medium | `--breakpoint-md` | `breakpoints.md` | `768px` | Tablet |
| Large | `--breakpoint-lg` | `breakpoints.lg` | `1024px` | Desktop |

Nota: las variables `--breakpoint-*` son custom properties CSS estándar, por lo que **no son usables dentro de `@media`** (limitación conocida de CSS — los media queries no interpolan `var()`). Para lógica de breakpoints en JS (`matchMedia`, hooks de resize, etc.) usar el objeto `breakpoints` exportado desde `tokens.ts`.

Todos los valores fueron validados contra WCAG AA (ratio ≥4.5:1 para texto normal, ≥3:1 para texto grande y elementos gráficos) — ver `src/__tests__/contrast.test.ts` para la verificación automatizada de los pares documentados arriba.
