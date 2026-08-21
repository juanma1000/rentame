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

## Tokens de estilo

| Token | Variable CSS | Constante TS | Valor | Uso |
| --- | --- | --- | --- | --- |
| Radio de tarjeta | `--radius-card` | `radius.card` | `10px` | Esquinas de tarjetas y superficies — sobrio, no redondeado tipo startup (rango aceptado 10–12px) |

Todos los valores fueron validados contra WCAG AA (ratio ≥4.5:1 para texto normal, ≥3:1 para texto grande y elementos gráficos) — ver `src/__tests__/contrast.test.ts` para la verificación automatizada de los pares documentados arriba.
