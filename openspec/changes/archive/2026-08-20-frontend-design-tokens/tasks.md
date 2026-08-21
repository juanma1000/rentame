## 1. Scaffolding del paquete

- [x] 1.1 Crear `frontend/packages/design-tokens/` con `package.json` (`name: "@rentame/design-tokens"`, `private: true`, `main`/`types` apuntando a `src/index.ts`), siguiendo el patrón de `packages/auth`
- [x] 1.2 Crear `tsconfig.json` extendiendo `frontend/tsconfig.base.json` (igual que `packages/auth`)
- [x] 1.3 Crear `eslint.config.mjs` reutilizando la config compartida del monorepo

## 2. Tokens de color

- [x] 2.1 Crear `src/tokens.css` con las variables CSS de color (`--color-primary: #0F172A`, `--color-primary-2: #1E3A5F`, `--color-accent: #C8A96B`, `--color-background: #F7F4ED`, `--color-surface: #FFFFFF`, `--color-text: #111827`, `--color-text-secondary: #64748B`, `--color-border: #E5E1D8`, `--color-success: #3F7D58`, `--color-error: #B94A48`) y `--radius-card: 10px` (rango 10–12px, valor base 10px)
- [x] 2.2 Crear `src/tokens.ts` con las mismas constantes tipadas en TypeScript (`export const colors = {...} as const`, `export const radius = {...} as const`)
- [x] 2.3 Crear `src/index.ts` que re-exporta `tokens.ts` (el `.css` se importa directamente por path desde los consumidores)

## 3. Documentación de reglas de uso

- [x] 3.1 Crear `README.md` del paquete documentando cada token, su valor, y su regla de uso derivada del análisis de contraste WCAG: dorado (`--color-accent`) solo como acento (bordes, íconos, badges de verificado/destacado, hover), nunca como fondo sólido con texto blanco — si se necesita fill sólido, usar texto `--color-primary` encima; `--color-text-secondary` solo sobre `--color-surface`, nunca directo sobre `--color-background`
- [x] 3.2 Referenciar el README del paquete desde `docs/frontend-standards.md` para que sea visible al escribir componentes nuevos

## 4. Verificación de contraste

- [x] 4.1 Escribir un test (Jest, sin DOM) que calcule el ratio de contraste WCAG entre los pares de tokens documentados en el README (texto/fondo, texto secundario/superficie, dorado/superficie) y falle si algún par por debajo del mínimo declarado se usa incorrectamente en la documentación
- [x] 4.2 Ejecutar el test y confirmar que los pares válidos (Text/Background, Text/Surface, SecondaryText/Surface, Primary Navy/Accent Gold, Surface/Primary, Surface/Success, Surface/Error) pasan AA (≥4.5:1 texto normal / ≥3:1 elementos gráficos)

## 5. Integración en los módulos consumidores

- [x] 5.1 Agregar `@rentame/design-tokens` como dependencia de workspace en `frontend/shell/package.json`
- [x] 5.2 Agregar `@rentame/design-tokens` como dependencia de workspace en `frontend/inmuebles-app/package.json`
- [x] 5.3 Importar `tokens.css` en el entrypoint de `shell` (`src/main.tsx` o `bootstrap.tsx`) para que las CSS variables estén disponibles globalmente
- [x] 5.4 Verificar manualmente (o con un test de smoke) que un elemento en `shell` renderiza usando `var(--color-primary)` con el valor `#0F172A` esperado

## 6. Cierre

- [x] 6.1 Correr lint y build de `shell` e `inmuebles-app` para confirmar que la nueva dependencia no rompe Module Federation ni el build de Rspack
- [ ] 6.2 Actualizar `openspec/specs/` ejecutando el sync de specs de este change una vez validado (fuera de este tasks.md, vía `/opsx:sync` o `/opsx:archive`)
