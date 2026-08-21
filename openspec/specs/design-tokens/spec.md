# design-tokens

## Purpose

TBD: provee un paquete compartido de tokens de diseño (color, radios de borde y reglas de uso por contraste) consumido por los módulos federados del frontend (`shell`, `inmuebles-app` y futuros módulos) para garantizar consistencia visual y cumplimiento de accesibilidad WCAG.

## Requirements

### Requirement: Paquete compartido de tokens de color
El sistema SHALL exponer un paquete `frontend/packages/design-tokens` que publica los valores de color de marca (Primary Navy `#0F172A`, Primary 2 Azul Petróleo `#1E3A5F`, Accent Dorado Champagne `#C8A96B`, Background Beige `#F7F4ED`, Surface Blanco `#FFFFFF`, Text `#111827`, Secondary Text `#64748B`, Border `#E5E1D8`, Success `#3F7D58`, Error `#B94A48`) como variables CSS y constantes TypeScript, para que `shell`, `inmuebles-app` y cualquier módulo federado futuro los consuman sin duplicar valores.

#### Scenario: Un módulo federado importa los tokens
- **WHEN** un módulo (`shell`, `inmuebles-app` u otro) declara `@rentame/design-tokens` como dependencia e importa un token de color
- **THEN** obtiene el valor hex correcto definido en el paquete, sin necesidad de redefinirlo localmente

#### Scenario: Cambio de un valor de marca se propaga sin tocar los módulos
- **WHEN** se actualiza un valor de color dentro del paquete `design-tokens`
- **THEN** los módulos que lo consumen reflejan el nuevo valor tras reconstruir, sin editar su propio código de estilos

### Requirement: Reglas de uso por contraste WCAG
El sistema SHALL documentar, junto a cada token de color, reglas de uso derivadas de validación de contraste WCAG AA, de forma que ningún componente combine tokens en una relación de contraste que falle el mínimo aplicable (4.5:1 para texto normal, 3:1 para texto grande y elementos gráficos).

#### Scenario: Texto secundario sobre el fondo de página
- **WHEN** se necesita mostrar texto en `Secondary Text (#64748B)`
- **THEN** la documentación del token indica que solo debe usarse sobre `Surface Blanco (#FFFFFF)`, nunca directo sobre `Background Beige (#F7F4ED)`, porque esa combinación no alcanza 4.5:1

#### Scenario: Uso del dorado como fondo de botón
- **WHEN** un desarrollador consulta cómo aplicar `Accent Dorado Champagne (#C8A96B)`
- **THEN** la documentación indica que no debe usarse como fondo sólido con texto blanco encima (falla 3:1), y que su uso previsto es como acento puntual (bordes, íconos, badges de verificado/destacado) o como fondo con texto `Primary Navy (#0F172A)` si se requiere un fill sólido

### Requirement: Tokens de estilo base complementarios
El sistema SHALL incluir, además de los colores, un valor base de `border-radius` para tarjetas (10–12px) como token compartido, evitando esquinas muy redondeadas no alineadas con la identidad "real estate premium sobrio" definida para el producto.

#### Scenario: Un componente de tarjeta usa el radio de borde compartido
- **WHEN** un módulo construye un componente de tarjeta (ej. tarjeta de propiedad)
- **THEN** usa el token de `border-radius` del paquete `design-tokens` en lugar de un valor arbitrario definido localmente
