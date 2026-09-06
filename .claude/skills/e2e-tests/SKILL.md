---
name: e2e-tests
description: Genera escenarios BDD en formato Gherkin (Feature + Scenarios) a partir de una historia de usuario (HU) del proyecto, buscándola por nombre o número en /docs/user-stories. Usa esta skill siempre que el usuario pida "generar Gherkin", "escenarios BDD", "feature file", "step definitions" a partir de una HU, o mencione una historia de usuario por su identificador (ej. "HU-023", "genera el feature de filtrar candidatos"). También aplica cuando el usuario pida cobertura de casos como caso feliz, caso vacío, filtro inválido o combinación de filtros para una funcionalidad ya documentada como historia de usuario.
---

# HU to Gherkin

Convierte una historia de usuario documentada en `/docs/user-stories` en un archivo `.feature` con escenarios Gherkin, listo para ejecutarse con **playwright-bdd**.

## Parámetro de entrada

El usuario invoca esta skill pasando el **nombre o identificador de la HU** (ej. `HU-023`, `filtrar-candidatos-por-fase`, o una descripción parcial como "filtrar candidatos"). Si el usuario no da ningún identificador, pregúntale cuál HU quiere procesar antes de continuar — no asumas cuál es.

## Paso 1: Localizar la HU

Busca el archivo correspondiente dentro de `${CLAUDE_PROJECT_DIR}/docs/user-stories` (o `/docs/user-stories` si `CLAUDE_PROJECT_DIR` no está definida):

1. Coincidencia exacta de nombre de archivo (con o sin extensión `.md`).
2. Si no hay coincidencia exacta, búsqueda difusa por número de HU o palabras clave del título dentro de los archivos del directorio (`grep -ril` sobre el texto de la historia).
3. Si hay múltiples candidatos, lista las opciones encontradas (ruta + primera línea) y pide al usuario que confirme cuál usar.
4. Si no se encuentra ningún archivo, informa la ausencia y pregunta si el usuario quiere pegar el texto de la HU directamente en el chat en su lugar.

No inventes contenido de la HU. Todo el criterio de aceptación y el lenguaje de dominio deben salir del archivo encontrado.

## Paso 2: Extraer el lenguaje de dominio

De la HU extraé:
- El **rol** (quién actúa: manager, reclutador, candidato, etc.)
- La **acción/objetivo** de negocio (qué quiere lograr, en términos funcionales, nunca de UI)
- El **beneficio/razón** (para qué lo quiere)
- Cualquier **criterio de aceptación** explícito ya presente en el archivo (fases del proceso, filtros válidos, mensajes esperados, etc.). Si el archivo no detalla criterios de aceptación, infiere el mínimo necesario para cubrir los 4 tipos de escenario del paso 3, y márcalo explícitamente como supuesto al final de tu respuesta.

## Paso 3: Generar el `.feature`

Genera un archivo Gherkin cubriendo, como mínimo, estos 4 tipos de escenario (a menos que la HU no aplique alguno, en cuyo caso omítelo y dilo):

1. **Caso feliz** — el filtro/acción se aplica y devuelve resultados esperados.
2. **Sin resultados en la condición dada** — ej. no hay candidatos en la fase filtrada.
3. **Entrada/filtro inválido** — valor de filtro que no corresponde a ninguna fase o formato válido del dominio.
4. **Combinación de filtros/condiciones** — dos o más criterios aplicados a la vez.

### Reglas de redacción (obligatorias)

- **Un único `When` por escenario.** Todo lo demás va en `Given` (precondiciones/estado) o `Then` (resultado observable).
- **Lenguaje de dominio, no de UI.** Prohibido usar palabras como "click", "botón", "pantalla", IDs técnicos, selectores CSS, nombres de componentes de código. En su lugar: "el manager filtra los candidatos por la fase 'Entrevista técnica'", no "el manager hace click en el dropdown de fase".
- **`Scenario Outline` + `Examples`** cuando dos o más escenarios comparten la misma estructura y solo cambian los valores (por ejemplo, distintas fases válidas, o distintos filtros inválidos). Usa `Scenario` simple solo cuando el caso es único.
- **Idioma**: redacta el Gherkin en el mismo idioma en que está escrita la HU (por defecto, español), salvo que el usuario pida explícitamente inglés. Las palabras clave de Gherkin (`Feature`, `Scenario`, `Given`, `When`, `Then`, `And`) pueden usarse en español (`Característica`, `Escenario`, `Dado`, `Cuando`, `Entonces`, `Y`) si el resto del código del proyecto usa ese estilo; si no sabes cuál convención sigue el proyecto, revisa otros `.feature` existentes en el repo antes de decidir, y si no hay ninguno, usa las palabras clave en inglés (más compatible con tooling) y el texto de los pasos en español.
- El nombre del archivo generado debe ser descriptivo y en kebab-case, ej. `filtrar-candidatos-por-fase.feature`.

### Estructura esperada

```gherkin
Feature: <nombre funcional de la HU, en lenguaje de negocio>
  Como <rol>
  Quiero <objetivo>
  Para <beneficio>

  Scenario: <caso feliz>
    Given <precondición>
    When <única acción>
    Then <resultado esperado>

  Scenario: <sin resultados>
    ...

  Scenario Outline: <filtro inválido / combinación, si aplica>
    Given <precondición>
    When <única acción con <placeholder>>
    Then <resultado con <placeholder>>

    Examples:
      | placeholder | ... |
      | valor1      | ... |
```

## Paso 4: Entregar el archivo

- El único destino válido del archivo `.feature` es `${CLAUDE_PROJECT_DIR}/test/features/` (o `/test/features` si `CLAUDE_PROJECT_DIR` no está definida). No lo entregues en ningún otro directorio ni lo dupliques en outputs sueltos.
- Si `test/features/` no existe todavía en el proyecto, créala.
- Este proyecto usa **playwright-bdd** (`playwright-bdd`) para ejecutar los escenarios Gherkin directamente con Playwright como test runner. Por lo tanto:
  - El `.feature` debe quedar en una ubicación que el `defineBddConfig`/`featuresRoot` del proyecto pueda resolver — por eso `test/features/` es la ruta fija, sin subcarpetas adicionales salvo que el usuario lo pida.
  - No generes archivos de configuración de Playwright ni el `playwright.config.ts` — asumí que ya existen y están apuntando a `test/features`.
  - No generes los step definitions en este paso salvo que el usuario lo pida explícitamente. playwright-bdd los genera/vincula a partir del `.feature` en un paso posterior (`npx bddgen` o equivalente), tal como describe la HU original.
- Confirma al usuario la ruta final donde quedó el archivo.
- Si tomaste algún supuesto (paso 2), resúmelo brevemente después de entregar el archivo.

## Paso 5: Generar step definitions a partir de un `.feature` existente
 
Este flujo se activa cuando el usuario pide explícitamente los step definitions de un `.feature` (propio de este flujo, o ya generado en el Paso 4). No lo ejecutes automáticamente después del Paso 4 salvo que el usuario lo pida.
 
1. **Leer el `.feature`**: localiza y lee el archivo indicado dentro de `${CLAUDE_PROJECT_DIR}/test/features/` (ej. `test/features/login.feature`). Si el usuario da solo un nombre sin ruta, buscalo ahí primero antes de preguntar. Si no existe, avisa y no inventes su contenido.
2. **Revisar steps ya existentes**: antes de escribir nada, lee todos los archivos dentro de `${CLAUDE_PROJECT_DIR}/test/features/steps/`. Por cada línea `Given/When/Then` del `.feature`, verificá si ya existe una definición equivalente (mismo texto o mismo patrón con parámetros compatibles):
   - Si el step ya existe, **no lo dupliques** — reusalo tal cual y no lo vuelvas a definir en el nuevo archivo.
   - Si el step es nuevo, generá su definición.
   - Si el step es parecido pero no idéntico (ej. cambia solo un valor fijo en vez de ser un parámetro), evaluá si conviene generalizar el step existente con un parámetro en lugar de crear uno nuevo casi duplicado, y proponé esto al usuario en vez de decidirlo en silencio.
3. **Generar las definiciones en TypeScript** usando `playwright-bdd` (`createBdd` de `playwright-bdd`):
   - Un archivo de steps por feature (o el mismo archivo si el usuario ya tiene esa convención), ubicado en `${CLAUDE_PROJECT_DIR}/test/features/steps/`, nombrado en relación al feature (ej. `login.steps.ts` para `login.feature`).
   - Import y patrón base:
     ```ts
     import { createBdd } from 'playwright-bdd';
 
     const { Given, When, Then } = createBdd();
     ```
   - **Queries accesibles obligatorias**: dentro de cada step, localizá elementos con `getByRole` y `getByLabel` como primera opción (ej. `page.getByRole('button', { name: 'Iniciar sesión' })`, `page.getByLabel('Correo electrónico')`). Evitá selectores CSS, `getByTestId`, o XPath salvo que el elemento no tenga rol/label accesible razonable — en ese caso, decilo explícitamente como limitación en vez de usar el selector frágil sin comentario.
   - Los `Then` deben usar `expect` de `@playwright/test` con aserciones sobre el estado visible (texto, rol, valor), no sobre implementación interna.
   - Mantené la firma de cada step fiel al texto del `.feature`: mismos placeholders (`{string}`, `{int}`) donde el Gherkin usa comillas o valores variables.
4. **Entregar el archivo**: guardalo únicamente en `${CLAUDE_PROJECT_DIR}/test/features/steps/`. No lo dupliques en otras rutas. Al terminar, resumí qué steps se generaron como nuevos y cuáles se reutilizaron sin cambios.