# Rentame — Frontend Monorepo

Monorepo de microfrontends para la plataforma Rentame. Usa **npm workspaces**, **Rspack 2** y **Module Federation 2.0** (host + remotes).

---

## Estructura

```
frontend/
├── packages/
│   └── auth/          # @rentame/auth — singleton de sesión compartido vía MF2
├── shell/              # Host: router global, layout, punto de entrada de la app
└── inmuebles-app/      # Remote privado (HU-001/002): publicar, editar, mis inmuebles
```

Remotes futuros (a scaffoldear en las HUs correspondientes):
- `busqueda-app` (HU-003)
- `identidad-app` (HU-004)
- `arrendamiento-app` (HU-005)
- `pagos-app` (HU-006)

---

## Requisitos

- **Node.js >= 20**
- **npm >= 7** (workspaces)

---

## Levantar el entorno de desarrollo

```bash
# 1. Instalar dependencias desde la raíz del monorepo
cd frontend/
npm install

# 2. Levantar el backend (Postgres + MinIO + API) — ver backend/README o docker-compose.yml en la raíz del repo
cd ../backend && docker compose up -d && ./.venv/bin/uvicorn main:app --port 8000

# 3. Levantar el remote inmuebles-app (puerto 3001) — debe levantarse ANTES o junto con el shell,
#    ya que el shell lo carga en runtime vía Module Federation
cd frontend/inmuebles-app && npm start

# 4. Levantar el shell (puerto 3000), en otra terminal
cd frontend/shell && npm start
```

El shell queda disponible en `http://localhost:3000`. La ruta `/mis-inmuebles` (protegida por sesión) carga en runtime el remote `inmuebles-app` desde `http://localhost:3001/remoteEntry.js` — si ese servidor no está corriendo, la ruta falla al montar el remote.

---

## Correr los tests

```bash
# Todos los workspaces
npm test

# Solo @rentame/auth
npm test -w @rentame/auth

# Solo shell
npm test -w rentame-shell
```

---

## Limitación conocida — Login de desarrollo (tasks 11.3-11.4)

**El dominio `usuarios` no tiene UI de login todavía** (fuera del alcance de HU-001).

Para poder probar `inmuebles-app` y el shell autenticado durante el desarrollo de HU-001, el shell expone una **pantalla de "pegar token"** en la ruta `/`. El desarrollador debe obtener un JWT del backend manualmente y pegarlo ahí.

### Cómo obtener un JWT de desarrollo

```python
# Desde el directorio backend/, con el virtualenv activado:
from shared.infrastructure.auth.jwt_handler import create_access_token
import uuid

# Generar un UUID de propietario (o usar uno del seed de la DB de dev)
propietario_id = str(uuid.uuid4())

token = create_access_token(usuario_id=propietario_id, rol="propietario")
print(token)
```

O bien, usando el helper de test que ya existe en el backend:

```bash
cd backend/
python -c "
from shared.infrastructure.auth.jwt_handler import create_access_token
import uuid
print(create_access_token(usuario_id=str(uuid.uuid4()), rol='propietario'))
"
```

Pegá el token resultante en `http://localhost:3000/` para inicializar tu sesión de desarrollo.

> Esta pantalla se eliminará cuando el dominio `usuarios` tenga login real (fuera del alcance de HU-001, planificado para una HU futura).

---

## AuthProvider / useAuth / AuthGuard

Implementados y en uso por `shell` (layout privado) e `inmuebles-app`. `@rentame/auth` exporta:
- **Tipos**: `Role`, `JwtPayload`, `AuthSession`
- **Utilidades de sesión**: `storeSession`, `getSession`, `clearSession`, `decodeTokenPayload`
- **React**: `AuthProvider`, `useAuth` (lanza si se usa fuera de un `AuthProvider`), `AuthGuard` (renderiza `children` si hay sesión, o `fallback` si no — sin dependencia de `react-router`; el redirect concreto lo compone `shell` pasando `fallback={<Navigate to="/" />}`)

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Bundler | Rspack 2 |
| Module Federation | `@module-federation/enhanced` 2 (MF2) |
| Framework UI | React 19 |
| Router | React Router 8 |
| Tipado | TypeScript 7 |
| Tests | Jest 30 + React Testing Library 16 + `@swc/jest` |
| Linting | ESLint 10 + `@typescript-eslint` 8 |

---

## Arquitectura de Module Federation

El **shell** es el host. Cada dominio de negocio vive en su propio **remote** (proceso de build y despliegue independiente). El paquete `@rentame/auth` se comparte como **singleton** vía MF2 para garantizar una única instancia del contexto de sesión en runtime.

Ver `docs/architecture/architecture.md` para el diagrama completo.
