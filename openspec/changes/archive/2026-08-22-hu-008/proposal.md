## Why

Ninguna HU implementada hasta ahora (HU-001, HU-002, HU-007) tiene un flujo real de registro o login — el "usuario" se crea insertando una fila directo en la base de datos y el JWT se emite a mano con un script. Sin esta capacidad, nada de lo construido es usable por una persona real fuera de un entorno de desarrollo. Es la pieza fundacional que faltaba desde HU-001.

## What Changes

- Nueva capacidad `usuarios`: registro por rol (propietario, agente, inquilino) con email + contraseña, login que emite un JWT (access token, sin refresh), y una pantalla de entrada única que ofrece las 3 opciones de forma simétrica.
- El registro como agente no se considera completo hasta resolver el paso de agencia: crear una agencia nueva, o buscar y solicitar unirse a una existente (reutiliza el modelo de estados y las operaciones de dominio ya construidas en HU-007, sin agregar una máquina de estados nueva).
- Nuevo endpoint público de búsqueda de agencias por razón social o NIT (capacidad `agencias`, sin autenticación) — necesario para que el flujo de registro de agente pueda encontrar una agencia existente a la que unirse.
- Login rechaza credenciales inválidas (email inexistente o contraseña incorrecta) con un mensaje único, sin distinguir cuál dato falló.
- Frontend: la pantalla de entrada del `shell` (`TokenLoginPage`, herramienta de desarrollo) se reemplaza por un flujo real de registro/login. El paso de agencia del registro de agente reutiliza las páginas/servicios que ya existen en `agencias.api.ts`/`inmuebles-app` donde aplique.

**Fuera de alcance explícito** (no inventar): verificación de email, recuperación de contraseña, refresh tokens, cambio de rol posterior a una cuenta ya creada, multi-rol.

## Capabilities

### New Capabilities
- `usuarios`: registro por rol, login con email+contraseña, emisión de JWT (access token), rechazo de credenciales inválidas.

### Modified Capabilities
- `agencias`: ADDED requirement — búsqueda pública de agencias por razón social/NIT (nuevo endpoint de solo lectura, sin autenticación). No se modifica ningún requirement existente de `agencias` (creación, membresía, relaciones) — solo se agrega esta capacidad de búsqueda nueva.

## Impact

**Backend**
- Nuevo dominio `backend/usuarios/` (domain, application, infrastructure) con entidad `Usuario` (extiende la tabla `usuario` ya existente: agrega `password_hash`), casos de uso `registrar_usuario` (por rol) y `autenticar_usuario`, endpoints `POST /usuarios/registro` (o el path que se defina por rol) y `POST /usuarios/login`.
- El registro de agente orquesta, desde la capa de API de `usuarios` (nunca desde `usuarios/application`), las operaciones ya existentes de `agencias` (`crear_agencia`, `solicitar_ingreso`) — mismo patrón de "la orquestación cross-domain vive en la API" ya usado en HU-002 para `inmuebles`↔`agencias`.
- Nuevo endpoint de búsqueda pública en `agencias/infrastructure/api/router.py` (`GET /agencias/buscar?q=...`), sin tocar `agencias/application` ni `agencias/domain` salvo lo estrictamente necesario para la búsqueda (ej. un método de repositorio nuevo).
- El contrato del JWT (`sub`, `rol`) se mantiene compatible con lo que `shared/infrastructure/auth/dependencies.py` ya valida — `get_current_propietario`, `get_current_agente`, `get_current_publicador` no se modifican.

**Frontend / Microfrontends afectados**
- `shell`: reemplaza `TokenLoginPage` por la pantalla de entrada real (3 opciones) y los formularios de registro/login. Es el único microfrontend afectado en su capa de auth — el resto sigue consumiendo `@rentame/auth` sin cambios en su contrato público.
- `inmuebles-app`: sin cambios de código esperados — ya consume `useAuth()` de la misma forma.

**Plan de rollback**
- Backend: revertir el código de `usuarios` no requiere migración de rollback de datos más allá de la columna `password_hash` agregada a `usuario` (nullable, no rompe las filas de prueba existentes creadas manualmente). El endpoint de búsqueda de `agencias` es aditivo puro.
- Frontend: revertir el `shell` a `TokenLoginPage` es un cambio de código sin dependencias de datos.
