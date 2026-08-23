---
description: Estándares de desarrollo, mejores prácticas y convenciones de frontend para la aplicación React con arquitectura de microfrontends (Module Federation), incluyendo patrones de componentes, manejo de estado, lineamientos de UI/UX y prácticas de testing
globs: ["frontend/**/src/**/*.{js,jsx,ts,tsx}", "frontend/**/e2e/**/*.{ts,js}", "frontend/**/playwright.config.ts", "frontend/**/tsconfig.json", "frontend/**/rspack.config.ts", "frontend/**/package.json"]
alwaysApply: true
---

# Configuración y Mejores Prácticas del Proyecto Frontend

## Tabla de Contenidos

- [Resumen](#resumen)
- [Stack Tecnológico](#stack-tecnológico)
  - [Tecnologías Core](#tecnologías-core)
  - [Framework de UI](#framework-de-ui)
  - [Manejo de Estado y Flujo de Datos](#manejo-de-estado-y-flujo-de-datos)
  - [Framework de Testing](#framework-de-testing)
  - [Herramientas de Desarrollo](#herramientas-de-desarrollo)
- [Arquitectura de Microfrontends (Module Federation)](#arquitectura-de-microfrontends-module-federation)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Estándares de Código](#estándares-de-código)
  - [Convenciones de Nomenclatura](#convenciones-de-nomenclatura)
  - [Convenciones de Componentes](#convenciones-de-componentes)
  - [Manejo de Estado](#manejo-de-estado)
  - [Arquitectura de la Capa de Servicios](#arquitectura-de-la-capa-de-servicios)
- [Estándares de UI/UX](#estándares-de-uiux)
  - [Integración de Bootstrap](#integración-de-bootstrap)
  - [Manejo de Formularios](#manejo-de-formularios)
  - [Patrones de Navegación](#patrones-de-navegación)
  - [Accesibilidad](#accesibilidad)
- [Estándares de Testing](#estándares-de-testing)
  - [Testing End-to-End](#testing-end-to-end)
  - [Organización de Tests](#organización-de-tests)
- [Estándares de Configuración](#estándares-de-configuración)
  - [Configuración de TypeScript](#configuración-de-typescript)
  - [Configuración de ESLint](#configuración-de-eslint)
  - [Configuración de Entornos](#configuración-de-entornos)
- [Mejores Prácticas de Performance](#mejores-prácticas-de-performance)
  - [Optimización de Componentes](#optimización-de-componentes)
  - [Optimización de Bundle](#optimización-de-bundle)
  - [Eficiencia de API](#eficiencia-de-api)
- [Flujo de Trabajo de Desarrollo](#flujo-de-trabajo-de-desarrollo)
  - [Flujo de Git](#flujo-de-git)
  - [Scripts de Desarrollo](#scripts-de-desarrollo)
  - [Calidad de Código](#calidad-de-código)
- [Estrategia de Migración](#estrategia-de-migración)
  - [Adopción de React 19](#adopción-de-react-19)
  - [Migración a Rspack + Module Federation 2.0](#migración-a-rspack--module-federation-20)
  - [Migración a TypeScript](#migración-a-typescript)
  - [Modernización de Componentes](#modernización-de-componentes)

---

## Resumen

Este documento describe las mejores prácticas, convenciones y estándares usados en la aplicación frontend. El frontend está compuesto por **microfrontends independientes**, cada uno desplegable por separado y compartiendo librerías core (React, autenticación) vía Module Federation. Estas prácticas garantizan consistencia de código, mantenibilidad y una buena experiencia de desarrollo entre equipos que trabajan en microfrontends distintos.

## Stack Tecnológico

### Tecnologías Core
- **React 19**: Server Components estabilizados, Actions, y React Compiler (reduce la necesidad de `useMemo`/`useCallback` manual)
- **TypeScript**: Para type safety y mejor experiencia de desarrollo
- **Rspack + Module Federation 2.0**: Bundler basado en Rust y runtime de microfrontends (host + remotes); config prácticamente idéntica a Webpack, pero con builds 5-10x más rápidos
- **React Router v8**: Ruteo y navegación del lado del cliente

### Framework de UI
- **Bootstrap 5 + React Bootstrap**: Framework CSS para diseño responsive *(ajustar si el proyecto usa un design system propio — por ejemplo, uno basado en la paleta de marca corporativa en vez de Bootstrap puro)*
- **React Bootstrap Icons**: Librería de íconos
- **React DatePicker**: Componentes de selección de fecha
- **`@rentame/design-tokens`**: Paquete compartido con los tokens de color de marca, tipografía, spacing, radios, sombras, transiciones, z-index y breakpoints. Ver `frontend/packages/design-tokens/README.md` para el valor de cada token y sus reglas de uso derivadas de contraste WCAG (ej. qué colores no combinar) antes de escribir estilos nuevos en cualquier microfrontend
- **`@rentame/ui`**: Sistema de componentes de referencia (`Button`, `Badge`, `Input`/`Select`/`Textarea`, `PropertyCard`), consumido por `shell` e `inmuebles-app`. Usar estos componentes en vez de estilos inline o markup ad-hoc para cualquier UI nueva de botones, badges, campos de formulario o tarjetas de inmueble — ver `frontend/packages/ui/README.md` antes de extenderlo o de crear un componente ad-hoc equivalente

### Manejo de Estado y Flujo de Datos
- **React Hooks**: `useState`, `useEffect` para estado local
- **Singleton de autenticación compartido**: Módulo de auth expuesto vía Module Federation y consumido por todos los microfrontends (ver sección de arquitectura)
- **React Beautiful DND**: Funcionalidad de drag and drop
- **Axios**: Cliente HTTP para comunicación con la API

### Framework de Testing
- **Playwright**: Testing end-to-end (incluyendo Playwright MCP para ejecución agéntica durante `/opsx:apply`, según `openspec-tasks-mandatory-steps.md`)
- **Jest** + **React Testing Library**: Testing unitario y de componentes

### Herramientas de Desarrollo
- **ESLint**: Linting de código con reglas específicas de React
- **TypeScript**: Chequeo estático de tipos
- **Web Vitals**: Monitoreo de performance

## Arquitectura de Microfrontends (Module Federation)

- **Host (shell/portal)**: Aplicación contenedora que carga los remotes en runtime y define el ruteo global entre microfrontends.
- **Remotes**: Cada microfrontend se expone (`exposes`) como módulo remoto independiente, con su propio pipeline de build y despliegue.
- **Módulos compartidos (`shared`)**: `react`, `react-dom` y el singleton de autenticación (`@celsia/auth` o el paquete equivalente) deben declararse como `singleton: true` en la config de Module Federation para evitar múltiples instancias de React o de sesión en runtime.
- **Autenticación compartida**: El singleton de auth expone el estado de sesión/token a todos los remotes sin que cada uno implemente su propio flujo OAuth — solo consumen el contexto/hook expuesto por el host.
- **Independencia de despliegue**: Cada microfrontend debe poder desplegarse sin requerir un rebuild del host ni de los demás remotes, siempre que el contrato de `exposes`/`shared` no cambie.
- **Versionado de contratos**: Cualquier cambio en la interfaz pública de un remote (props expuestas, rutas, eventos) debe tratarse como un breaking change y comunicarse a los demás equipos antes de desplegar.

```javascript
// rspack.config.ts (remote) — ejemplo simplificado, MF2 sobre Rspack
import { ModuleFederationPlugin } from '@module-federation/enhanced/rspack';

export default {
  plugins: [
    new ModuleFederationPlugin({
      name: 'candidatesApp',
      filename: 'remoteEntry.js',
      exposes: {
        './CandidatesRoutes': './src/CandidatesRoutes',
      },
      shared: {
        react: { singleton: true, requiredVersion: false },
        'react-dom': { singleton: true, requiredVersion: false },
        '@celsia/auth': { singleton: true },
      },
    }),
  ],
};
```

> El único cambio real respecto a Webpack + MF1 es el import (`@module-federation/enhanced/rspack` en vez de `webpack.container.ModuleFederationPlugin`) — la forma de declarar `exposes`/`shared` se mantiene igual, lo que hace la migración bastante directa.

## Estructura del Proyecto

```
frontend/
├── shell/                      # Host: portal contenedor
│   ├── src/
│   │   ├── App.tsx
│   │   └── rspack.config.ts    # Config de Module Federation 2.0 (host)
│   └── package.json
├── candidates-app/              # Remote: microfrontend de candidatos
│   ├── src/
│   │   ├── components/         # Componentes de UI reutilizables
│   │   ├── services/           # Capa de servicios de API
│   │   ├── pages/               # Componentes de página
│   │   ├── assets/               # Imágenes, fuentes, recursos estáticos
│   │   ├── App.tsx
│   │   ├── index.tsx
│   │   └── rspack.config.ts    # Config de Module Federation 2.0 (remote)
│   ├── e2e/                     # Archivos de test end-to-end (Playwright)
│   │   └── playwright.config.ts
│   └── package.json
├── positions-app/                # Otro remote, misma estructura interna
└── packages/
    ├── auth/                     # @celsia/auth — singleton compartido
    └── design-tokens/            # @rentame/design-tokens — paleta y tokens de estilo compartidos
```

## Estándares de Código

### Convenciones de Nomenclatura

- **Nombres de componentes**: `PascalCase` (ej. `CandidateCard`, `PositionDetails`, `RecruiterDashboard`)
- **Variables y funciones**: `camelCase` (ej. `candidateId`, `handleSubmit`, `fetchPositions`)
- **Constantes**: `UPPER_SNAKE_CASE` (ej. `MAX_CANDIDATES_PER_PAGE`, `API_BASE_URL`)
- **Tipos/Interfaces**: `PascalCase` (ej. `CandidateData`, `PositionProps`, `ICandidateService`)
- **Nombres de archivo**: `PascalCase` para archivos de componente (ej. `CandidateCard.tsx`), `camelCase` para archivos de utilidades (ej. `candidateService.ts`, `apiUtils.ts`)
- **Nombres de clases CSS**: `kebab-case` (ej. `candidate-card`, `position-details`)
- **Nombres de hooks**: `camelCase` empezando con prefijo `use` (ej. `useCandidate`, `usePositionData`, `useFormValidation`)

**Ejemplos:**

```typescript
// Bien: todo en inglés
import React, { useState } from 'react';

type CandidateCardProps = {
    candidate: Candidate;
    index: number;
    onClick: (candidate: Candidate) => void;
};

const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, index, onClick }) => {
    const [isLoading, setIsLoading] = useState(false);

    // Handle candidate card click event
    const handleCardClick = () => {
        onClick(candidate);
    };

    return (
        <div className="candidate-card" onClick={handleCardClick}>
            {/* Component JSX */}
        </div>
    );
};

// Evitar: comentarios o nombres en español dentro del código
const TarjetaCandidato: React.FC<PropsTarjetaCandidato> = ({ candidato, indice, alHacerClic }) => {
    const [estaCargando, setEstaCargando] = useState(false);

    // Manejar evento de clic en la tarjeta de candidato
    const manejarClicTarjeta = () => {
        alHacerClic(candidato);
    };

    return (
        <div className="tarjeta-candidato" onClick={manejarClicTarjeta}>
            {/* JSX del componente */}
        </div>
    );
};
```

**Mensajes de error y console logs:**

```typescript
// Bien: mensajes de error en inglés
catch (error) {
    console.error('Failed to fetch candidates:', error);
    setError('Unable to load candidates. Please try again later.');
}

// Evitar: mensajes en español dentro del código
catch (error) {
    console.error('Error al obtener candidatos:', error);
    setError('No se pudieron cargar los candidatos.');
}
```

**Ejemplos de capa de servicios:**

```typescript
// Bien: nomenclatura en inglés en los servicios
export const candidateService = {
    getAllCandidates: async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/candidates`);
            return response.data;
        } catch (error) {
            console.error('Error fetching candidates:', error);
            throw error;
        }
    }
};

// Evitar: nomenclatura en español
export const servicioCandidatos = {
    obtenerTodosLosCandidatos: async () => {
        // ...
    }
};
```

### Convenciones de Componentes

#### Componentes Funcionales
- **Usar siempre componentes funcionales** con hooks, nunca componentes de clase
- Usar **TypeScript para componentes nuevos** siempre que sea posible
- Mantener **JavaScript en componentes legacy** hasta que se planifique su migración

```typescript
// Preferido - componente funcional en TypeScript
import React, { useState } from 'react';

type Position = {
    id: number;
    title: string;
    status: 'Open' | 'Hired' | 'Closed' | 'Draft';
};

const Positions: React.FC = () => {
    const [positions, setPositions] = useState<Position[]>([]);
    // Lógica del componente
};
```

#### Props de Componentes
- **Definir interfaces/types de TypeScript** para las props de cada componente
- Usar **destructuring** para las props
- Incluir **valores por defecto** donde tenga sentido

```typescript
type CandidateCardProps = {
    candidate: Candidate;
    index: number;
    onClick: (candidate: Candidate) => void;
};

const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, index, onClick }) => {
    // Implementación del componente
};
```

### Manejo de Estado

#### Estado Local con Hooks
- Usar **useState** para estado a nivel de componente
- Usar **useEffect** para efectos secundarios y fetching de datos
- **Extraer hooks custom** para lógica de estado reutilizable

```typescript
const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'Draft',
});

const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
        ...prev,
        [name]: value,
    }));
};
```

#### Estados de Carga y Error
- **Manejar siempre los estados de loading** para operaciones asíncronas
- **Implementar manejo de errores** con mensajes claros para el usuario
- **Usar componentes Alert de React Bootstrap** para el feedback (o el equivalente del design system del proyecto)

```typescript
const [loading, setLoading] = useState(true);
const [error, setError] = useState('');
const [success, setSuccess] = useState('');

// Dentro de una función async
try {
    setLoading(true);
    const data = await apiCall();
    setSuccess('Operation completed successfully');
} catch (error) {
    setError('Error message: ' + error.message);
} finally {
    setLoading(false);
}
```

### Arquitectura de la Capa de Servicios

#### Servicios de API
- **Centralizar las llamadas a la API** en archivos de servicio
- Usar **axios** para requests HTTP
- **Exportar objetos de servicio** con métodos agrupados
- **Manejar errores a nivel de servicio** cuando tenga sentido

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL;

export const positionService = {
    getAllPositions: async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/positions`);
            return response.data;
        } catch (error) {
            console.error('Error fetching positions:', error);
            throw error;
        }
    },

    updatePosition: async (id: number, positionData: Partial<Position>) => {
        try {
            const response = await axios.put(`${API_BASE_URL}/positions/${id}`, positionData);
            return response.data;
        } catch (error) {
            console.error('Error updating position:', error);
            throw error;
        }
    },
};
```

## Estándares de UI/UX

### Integración de Bootstrap

- Usar **componentes de React Bootstrap** en vez de Bootstrap plano *(o los componentes del design system corporativo si el proyecto ya migró a uno propio)*
- **Importar el CSS de Bootstrap** en el componente principal de cada microfrontend
- Seguir el **sistema de grilla responsive de Bootstrap** (Container, Row, Col)

```typescript
import { Container, Row, Col, Card, Button, Form, Alert } from 'react-bootstrap';
```

### Manejo de Formularios

- Usar **componentes controlados** para los inputs de formulario
- Implementar **validación en tiempo real** donde tenga sentido
- **Deshabilitar el botón de submit** durante el envío del formulario
- **Limpiar el estado del formulario** después de un envío exitoso

```typescript
<Form onSubmit={handleSubmit}>
    <Form.Group className="mb-3">
        <Form.Label>Title *</Form.Label>
        <Form.Control
            type="text"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            required
        />
    </Form.Group>
    <Button type="submit" disabled={saving}>
        {saving ? 'Saving...' : 'Save'}
    </Button>
</Form>
```

### Patrones de Navegación

- Usar **React Router** para toda la navegación dentro de cada microfrontend
- **Implementar breadcrumbs** con navegación hacia atrás
- Usar **navegación programática** con el hook `useNavigate`
- La navegación **entre microfrontends** distintos debe pasar por el router del host (shell), no por rutas hardcodeadas entre remotes

```typescript
import { useNavigate } from 'react-router';

const navigate = useNavigate();

<Button variant="link" onClick={() => navigate('/')}>
    ← Back to Dashboard
</Button>
```

### Accesibilidad

- Incluir atributos **aria-label** en elementos interactivos
- Usar elementos **HTML semánticos**
- Garantizar soporte de **navegación por teclado**
- Proveer **texto alternativo** para imágenes

```typescript
<Form.Control
    type="text"
    placeholder="Search by title"
    aria-label="Search positions by title"
/>
```

## Estándares de Testing

### Testing End-to-End

- **Probar flujos de usuario**, no detalles de implementación
- Usar atributos **data-testid** para selección confiable de elementos (`page.getByTestId(...)`)
- **Organizar los tests por feature** (`candidates.spec.ts`, `positions.spec.ts`)
- **Incluir testing de API** junto con el testing de UI, usando el contexto de request de Playwright (`request` fixture) para llamadas directas cuando no haga falta pasar por la UI
- Para flujos que cruzan microfrontends (ej. login en el shell → navegación a un remote), probar el flujo completo end-to-end, no cada microfrontend de forma aislada
- Cuando el agente ejecute estos tests durante `/opsx:apply`, debe usar las herramientas de **Playwright MCP** (`browser_navigate`, `browser_click`, `browser_type`, `browser_snapshot`, etc.) en vez de escribir y correr el archivo de test directamente, según lo definido en `openspec-tasks-mandatory-steps.md`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Positions API - Update', () => {
    test.beforeEach(async ({ page }) => {
        await page.evaluate(() => window.localStorage.clear());
    });

    test('should update a position successfully', async ({ request }) => {
        const updateData = {
            title: 'Updated Test Position',
            status: 'Open',
        };

        const response = await request.put(
            `${process.env.API_URL}/positions/${testPositionId}`,
            { data: updateData },
        );

        expect(response.status()).toBe(200);
        const body = await response.json();
        expect(body.data.title).toBe(updateData.title);
    });
});
```

### Organización de Tests

- **Agrupar tests relacionados** con bloques `describe`
- **Usar nombres de test descriptivos** que expliquen el comportamiento esperado
- **Probar tanto escenarios exitosos como de error**
- **Incluir edge cases** y testing de validación

## Estándares de Configuración

### Configuración de TypeScript

- Habilitar **modo strict** para el chequeo de tipos
- Usar **path mapping** con `"@/*"` para imports más limpios
- Incluir los **tipos de Node** (Playwright trae sus propios tipos vía `@playwright/test`, no requiere una entrada separada en `types`)
- Cada microfrontend mantiene su propio `tsconfig.json`, extendiendo una configuración base compartida si el monorepo lo permite

```json
{
    "compilerOptions": {
        "strict": true,
        "baseUrl": ".",
        "paths": {
            "@/*": ["src/*"]
        },
        "types": ["node"]
    }
}
```

### Configuración de ESLint

- Extender la configuración de **React**
- Incluir **reglas de Jest** para testing
- **Formateo automático** y detección de errores
- **Estilo de código consistente** en todos los microfrontends (misma config base compartida vía paquete interno)

### Configuración de Entornos

- Usar **variables de entorno** para las URLs de API
- **Configuraciones separadas** para desarrollo y producción
- Configurar **Playwright** con settings específicos por entorno
- Cada microfrontend define su propia URL de `remoteEntry.js` por entorno (dev/UAT/prod), inyectada vía variable de entorno del pipeline

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
    use: {
        baseURL: process.env.BASE_URL || 'http://localhost:3000',
    },
    projects: [
        { name: 'chromium', use: { browserName: 'chromium' } },
    ],
});
```

## Mejores Prácticas de Performance

### Optimización de Componentes

- **Lazy load** de componentes y de microfrontends remotos cuando aplique
- **Memoizar cálculos costosos** con `useMemo`
- **Evitar re-renders innecesarios** con `useCallback`
- **Extraer lógica reutilizable** en hooks custom

### Optimización de Bundle

- **Tree shaking** habilitado en la config de Rspack
- **Code splitting** a nivel de ruta y de remote (Module Federation ya aporta code splitting entre microfrontends por diseño)
- **Optimizar imágenes** y assets estáticos
- **Monitorear el tamaño del bundle** de cada microfrontend por separado, no solo del host

### Eficiencia de API

- **Implementar manejo de errores apropiado** para requests de red
- **Cachear respuestas de API** donde tenga sentido
- **Usar estados de loading** para mejorar la performance percibida
- **Agrupar llamadas a la API** cuando sea posible

## Flujo de Trabajo de Desarrollo

- **Feature branches**: Desarrollar features en ramas separadas, agregando el sufijo descriptivo `-frontend` (o el nombre del microfrontend específico, ej. `-candidates-app`) para permitir trabajo en paralelo y evitar conflictos
- **Commits descriptivos**: Escribir mensajes de commit descriptivos en inglés
- **Code review**: Revisión de código antes de mergear
- **Ramas pequeñas**: Mantener las ramas pequeñas y focalizadas

### Scripts de Desarrollo

```bash
npm start                  # Servidor de desarrollo (del microfrontend actual)
npm test                   # Correr tests unitarios
npm run build               # Build de producción
npx playwright test --ui     # Abrir el test runner de Playwright (modo UI)
npx playwright test          # Correr los tests de Playwright en modo headless
```

### Calidad de Código

- **Validación con ESLint** antes de cada commit
- **Compilación de TypeScript** sin errores
- **Todos los tests pasando** antes de desplegar
- **Monitoreo de performance** con Web Vitals

## Estrategia de Migración

### Adopción de React 19

- **React Compiler**: Habilitarlo progresivamente, componente por componente — permite eliminar gran parte de los `useMemo`/`useCallback` manuales sin reescribir la lógica
- **Actions y Server Components**: Adoptar de forma incremental donde resuelvan un problema real (formularios con estado optimista, data fetching), no como reescritura masiva
- **Codemods oficiales**: Usar las herramientas de migración oficiales de React para el upgrade 18 → 19 antes de tocar patrones nuevos

### Migración a Rspack + Module Federation 2.0

- **Migrar host y remotes en el mismo ciclo**: dado que comparten el contrato de `shared`/`exposes`, evitar tener unos microfrontends en Webpack/MF1 y otros en Rspack/MF2 al mismo tiempo por más de un sprint
- **Cambio mínimo de config**: el `shared`/`exposes`/`remotes` se mantiene igual; solo cambia el import del plugin y el bundler subyacente
- **Validar el singleton de auth primero**: al ser compartido por todos los remotes, es el punto de mayor riesgo — probarlo aislado antes de migrar el resto

### Migración a TypeScript

- **Migración gradual** de JavaScript a TypeScript
- **Componentes nuevos en TypeScript** por defecto
- **Mantener el JavaScript existente** hasta que se planifique el refactor
- **Agregar tipos incrementalmente** al código existente

### Modernización de Componentes

- **Componentes funcionales** en vez de componentes de clase
- **Hooks** en vez de lifecycle methods
- **Componentes de React Bootstrap** (o del design system corporativo) para consistencia visual entre microfrontends
- Principios de **diseño responsive** en todos los remotes

Este documento sirve como base para mantener la calidad y consistencia del código en toda la aplicación frontend. Todo el equipo debe seguir estas prácticas para asegurar un código base mantenible y escalable entre los distintos microfrontends.