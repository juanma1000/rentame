## Why

El frontend (monorepo con Module Federation: `shell`, `inmuebles-app`, y el futuro módulo de agencias de HU-007) no tiene ningún sistema de theming: no hay Tailwind, ni CSS global, ni tokens de color compartidos. Cada módulo estilaría de forma independiente y ad-hoc, lo que produciría inconsistencia visual entre remotes y duplicación de valores de color a medida que crezcan las pantallas por rol (público, inquilino, propietario, agente/agencia). Se definió una paleta de marca (navy, azul petróleo, dorado champagne, beige) durante una sesión de exploración, incluyendo validación de contraste WCAG y reglas de uso por color; corresponde ahora fijar esos valores como tokens compartidos antes de que cualquier módulo empiece a construir UI sobre ellos.

## What Changes

- Se crea un paquete nuevo `frontend/packages/design-tokens` (siguiendo el precedente de `packages/auth`) que exporta los tokens de color de marca como variables CSS/JS.
- Se documentan reglas de uso por token (ej. dorado solo como acento, nunca fondo de botón con texto claro; texto secundario solo sobre superficies blancas) para que los equipos de `shell`, `inmuebles-app` y futuros módulos las apliquen de forma consistente.
- Se fijan valores base de estilo compartidos que acompañan a la paleta: `border-radius` de tarjetas (10–12px) y familia tipográfica base (a definir en design.md).
- `shell` e `inmuebles-app` consumen el paquete `design-tokens` como dependencia, sin duplicar valores de color localmente.
- No se migra ni redistribuye ningún estilo visual existente de pantallas ya implementadas (HU-001) — esto es alcance de una change futura si aplica; este change solo publica el paquete de tokens y lo deja disponible para consumo.

## Capabilities

### New Capabilities
- `design-tokens`: paquete compartido de tokens de color y estilo base (radios, uso por rol/color) para los módulos federados del frontend, con reglas de contraste WCAG AA validadas.

### Modified Capabilities
(ninguna — no se modifican requisitos de capacidades existentes; `inmuebles` no cambia su comportamiento funcional, solo pasaría a consumir el paquete en una tarea de integración incluida en tasks.md)

## Impact

- **Código afectado**: nuevo paquete `frontend/packages/design-tokens/`; cambios de configuración en `shell` e `inmuebles-app` (package.json, rspack shared config) para consumir el paquete.
- **Microfrontends/equipos afectados**: `shell`, `inmuebles-app`, y el futuro módulo de agencias (HU-007) hereda el paquete al construirse.
- **Dependencias**: ninguna dependencia externa nueva (tokens en CSS variables / TS puro, sin librería de theming de terceros).
- **Rollback**: el paquete es aditivo y no reemplaza estilos existentes; revertir consiste en quitar la dependencia del paquete en los `package.json` de `shell`/`inmuebles-app` y eliminar el paquete — no hay migración de datos ni cambios de contrato de API involucrados.
