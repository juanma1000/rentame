## Context

El frontend es un monorepo con Module Federation 2.0: `shell` (host) e `inmuebles-app` (remote), más `packages/auth` como paquete compartido ya existente que consumen ambos. No existe hoy ningún sistema de theming: no hay Tailwind, CSS global, ni tokens. HU-007 (gestión de agencias) está en progreso y eventualmente tendrá su propia UI (probablemente un nuevo remote), que también necesitará estos tokens.

Durante una sesión de exploración se definió una paleta de marca (navy, azul petróleo, dorado champagne, beige) y se validó su contraste con WCAG AA, encontrando tres ajustes de uso necesarios (dorado no apto como fill con texto blanco, texto secundario no apto sobre el fondo beige, borde casi invisible sobre el fondo beige). Este design.md fija cómo se empaquetan y distribuyen esos tokens.

## Goals / Non-Goals

**Goals:**
- Publicar un único paquete (`@rentame/design-tokens`) como fuente de verdad de los valores de color de marca y del `border-radius` base.
- Que `shell` e `inmuebles-app` puedan consumir el paquete sin duplicar valores hex en su propio código.
- Documentar, junto a los tokens, las reglas de uso derivadas del análisis de contraste, para que futuros componentes (incluida la UI de agencias de HU-007) no repitan los mismos errores de contraste.

**Non-Goals:**
- No se construye una librería de componentes visuales (botones, tarjetas, etc.) en este change — solo los tokens primitivos y sus reglas de uso.
- No se migran estilos de pantallas ya existentes de HU-001 a los nuevos tokens; eso es una tarea de adopción posterior, fuera de este alcance.
- No se decide aquí el sistema tipográfico completo ni un theme oscuro — solo la paleta de color y el radio de borde ya acordados.
- No se introduce Tailwind ni ninguna librería de CSS-in-JS; los tokens se publican como CSS variables + constantes TypeScript planas, sin dependencia de terceros.

## Decisions

### 1. Formato de los tokens: CSS variables + constantes TypeScript, sin librería de theming
Se exportan los tokens en dos formas desde el mismo paquete:
- Un archivo `tokens.css` con `:root { --color-primary: #0F172A; ... }`, para consumo directo en CSS/CSS Modules de cualquier módulo.
- Un módulo TypeScript (`tokens.ts`) con las mismas constantes tipadas, para casos donde se necesite el valor en JS/TS (ej. props de gráficos, canvas, lógica condicional de UI).

**Alternativas consideradas**: usar una librería de design tokens (Style Dictionary, Theo) fue descartado por sobre-ingeniería para 10 colores y un radio — no hay múltiples plataformas de salida (solo web) ni necesidad de transformación multi-formato. Tailwind con `theme.extend.colors` fue descartado porque el proyecto no usa Tailwind hoy y adoptarlo es una decisión mayor fuera del alcance de este change.

### 2. Ubicación: paquete nuevo `frontend/packages/design-tokens`
Sigue el precedente de `packages/auth`: un paquete independiente en el workspace que `shell` e `inmuebles-app` declaran como dependencia. Evita que el `shell` sea el dueño del theme (lo que forzaría a los remotes a depender del host para algo tan básico como un color), y deja el paquete disponible para el futuro remote de agencias sin acoplarlo a `shell` o a `inmuebles-app`.

**Alternativa considerada**: exponer los tokens desde `shell` vía Module Federation `shared`. Descartada porque invierte la dependencia (un remote como `inmuebles-app` dependería del host para sus colores) y complica la carga cuando un módulo se ejecuta de forma aislada (ej. en tests unitarios de `inmuebles-app` sin el shell arriba).

### 3. Las reglas de uso viven como documentación junto al paquete, no como validación en runtime
Las reglas (“dorado no como fill+texto blanco”, “texto secundario solo sobre blanco”) se documentan en un `README.md` del paquete y en comentarios en `tokens.css`/`tokens.ts`, no como un linter o validación automática de combinaciones de color.

**Alternativa considerada**: un lint rule custom de ESLint que bloquee combinaciones de contraste inválidas. Descartado por complejidad desproporcionada al tamaño del problema (10 tokens, reglas ya conocidas); si en el futuro surgen violaciones recurrentes, se puede revisar.

## Risks / Trade-offs

- **[Riesgo] Los módulos ignoran las reglas de uso documentadas y las violan de todos modos** (ej. alguien pone texto blanco sobre dorado) → Mitigación: las reglas quedan en el README del paquete junto a cada token, y quedan referenciadas en `docs/frontend-standards.md` para que sea visible al momento de escribir cualquier componente nuevo.
- **[Riesgo] Al no migrar HU-001 a los nuevos tokens, queda una inconsistencia temporal entre pantallas viejas (sin tokens) y nuevas (con tokens)** → Mitigación aceptada como trade-off consciente: es preferible publicar los tokens ahora y adoptarlos incrementalmente que bloquear este change con una migración retroactiva de mayor alcance.
- **[Riesgo] Sin build tooling propio, el paquete podría no integrarse limpiamente con Rspack/Module Federation de `shell`/`inmuebles-app`** → Mitigación: el paquete se mantiene simple (CSS + TS plano, sin paso de build propio más allá de `tsc` para tipos), replicando la configuración ya probada de `packages/auth`.

## Migration Plan

1. Crear el paquete `frontend/packages/design-tokens` con `tokens.css`, `tokens.ts` y `README.md` con las reglas de uso.
2. Agregar `@rentame/design-tokens` como dependencia en `shell` e `inmuebles-app` (package.json + referencia en su config de build si aplica).
3. Verificar que ambos módulos puedan importar y renderizar un token de prueba (ej. aplicar `--color-primary` a un elemento visible) antes de dar por cerrado el change.

**Rollback**: quitar la dependencia `@rentame/design-tokens` de los `package.json` de `shell`/`inmuebles-app` y eliminar el paquete. Al ser aditivo (no reemplaza estilos existentes de HU-001), no hay estado ni datos que revertir.

## Open Questions

- ¿Se necesita un tema oscuro a futuro? No está en alcance de este change; si surge, el paquete puede extenderse con un segundo set de variables bajo `[data-theme="dark"]`.
- ¿La UI de agencias (HU-007) tendrá su propio remote federado o vivirá dentro de `inmuebles-app`? No afecta el diseño de este paquete (es agnóstico al remote que lo consuma), pero queda pendiente de la definición de arquitectura de HU-007.
