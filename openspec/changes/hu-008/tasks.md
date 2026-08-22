## 0. Setup: Crear Feature Branch Backend (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/hu-008-backend` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: Migración y modelo de dominio `usuarios`

- [x] 1.1 Migración Alembic: agregar `password_hash` (nullable) y `nombre` (nullable) a la tabla `usuario`
- [x] 1.2 qa-expert (Red): tests unitarios de `Usuario` — hash/verificación de contraseña con `bcrypt`, `password_hash` nunca serializado
- [x] 1.3 backend-expert (Green): entidad `Usuario` en `backend/usuarios/domain/usuario.py` con métodos `crear(email, password, nombre, rol)` y `verificar_password(password)`
- [x] 1.4 backend-expert: excepciones de dominio `EmailYaRegistrado`, `CredencialesInvalidas` en `backend/usuarios/domain/exceptions.py`

## 2. Backend: Casos de uso de registro y login

- [x] 2.1 qa-expert (Red): tests de `registrar_usuario` con fake repository — rechaza email duplicado, crea con rol fijo, hashea la contraseña
- [x] 2.2 backend-expert (Green): `backend/usuarios/application/registrar_usuario.py`
- [x] 2.3 qa-expert (Red): tests de `autenticar_usuario` con fake repository — éxito devuelve `Usuario`, email inexistente y contraseña incorrecta levantan la misma `CredencialesInvalidas`
- [x] 2.4 backend-expert (Green): `backend/usuarios/application/autenticar_usuario.py`
- [x] 2.5 backend-expert: puerto `UsuarioRepositoryPort` (`crear`, `buscar_por_email`) en `backend/usuarios/domain/ports.py`

## 3. Backend: Persistencia `usuarios`

- [x] 3.1 backend-expert: actualizar `UsuarioORM` en `backend/usuarios/infrastructure/persistence/models.py` con `password_hash`, `nombre`
- [x] 3.2 qa-expert (Red): tests de integración de `UsuarioRepositoryPostgres` contra Postgres real (crear, buscar por email, unicidad de email)
- [x] 3.3 backend-expert (Green): `backend/usuarios/infrastructure/persistence/repository.py`

## 4. Backend: Endpoints `usuarios`

- [x] 4.1 qa-expert (Red): tests de integración `POST /usuarios/registro` — cubre los 3 roles, rechazo de email duplicado, validación 422
- [x] 4.2 backend-expert (Green): `backend/usuarios/infrastructure/api/router.py` + `schemas.py` — `POST /usuarios/registro`
- [x] 4.3 qa-expert (Red): tests de integración `POST /usuarios/login` — éxito emite JWT con `sub`/`rol`, credenciales inválidas rechazadas con mensaje único
- [x] 4.4 backend-expert (Green): `POST /usuarios/login` reutilizando `jwt_handler.create_access_token` (sin modificarlo)
- [x] 4.5 backend-expert: registrar el router de `usuarios` en `backend/main.py`

## 5. Backend: Búsqueda pública de agencias

- [x] 5.1 qa-expert (Red): tests unitarios de caso de uso `buscar_agencias` (fake repository) — coincidencia por razón social/NIT, sin resultados devuelve lista vacía
- [x] 5.2 backend-expert (Green): `backend/agencias/application/buscar_agencias.py`
- [x] 5.3 qa-expert (Red): test de integración de `AgenciaRepositoryPostgres.buscar(texto)` contra Postgres real
- [x] 5.4 backend-expert (Green): método `buscar` en `AgenciaRepositoryPort`/`AgenciaRepositoryPostgres`
- [x] 5.5 qa-expert (Red): test de integración `GET /agencias/buscar?q=...` — sin autenticación, devuelve solo datos públicos
- [x] 5.6 backend-expert (Green): endpoint `GET /agencias/buscar` en `backend/agencias/infrastructure/api/router.py` + schema de respuesta pública

## 6. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 6.1 Revisar suite completa de `backend/tests/` en busca de fixtures/tests afectados por las nuevas columnas de `usuario` o el nuevo endpoint de `agencias`
- [x] 6.2 Actualizar fixtures de `conftest.py` que creen usuarios de prueba para incluir `password_hash`/`nombre` donde corresponda (revisadas `seed_propietario`/`seed_agente` en `backend/tests/conftest.py`: ambas columnas son nullable y ningún test existente depende de ellas, no requieren cambio)

## 7. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 7.1 Capturar el baseline de base de datos pre-test (conteo de filas en `usuario`, `agencia`)
- [x] 7.2 Correr los unit tests focalizados de `usuarios` y `agencias` vía `docker compose exec backend pytest backend/tests/usuarios backend/tests/agencias`
- [x] 7.3 Correr la suite completa vía `docker compose exec backend pytest`
- [x] 7.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [x] 7.5 Crear el reporte `openspec/changes/hu-008/specs/reports/YYYY-MM-DD-step-7-unit-test-and-db-verification.md`
- [x] 7.6 Marcar este paso como completo solo después de que los tests pasen y el reporte exista

## 8. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 8.1 Asegurar que `docker compose up` esté corriendo (backend + postgres)
- [x] 8.2 Testear `POST /usuarios/registro` con curl para los 3 roles (propietario, agente, inquilino) y verificar el JWT devuelto
- [x] 8.3 Testear `POST /usuarios/registro` con email duplicado y verificar el rechazo (400/409)
- [x] 8.4 Testear `POST /usuarios/login` con credenciales correctas e incorrectas, verificando el mensaje único de error
- [x] 8.5 Testear `GET /agencias/buscar?q=...` sin header de autenticación, con y sin coincidencias
- [x] 8.6 Testear el flujo completo de agente: registro → `POST /agencias/` con el JWT recién emitido → verificar membresía
- [x] 8.7 Restaurar el estado de la base de datos (eliminar usuarios/agencias de prueba creados)
- [x] 8.8 Documentar todos los comandos curl y respuestas en `openspec/changes/hu-008/specs/reports/YYYY-MM-DD-step-8-curl-manual-testing.md`

## 9. Setup: Crear Feature Branch Frontend

- [x] 9.1 Crear y cambiar al branch `feature/hu-008-shell` desde `feature/hu-008-backend` (aún no mergeado a `main`)
- [x] 9.2 Verificar la creación del branch y el estado del branch actual

## 10. Frontend: Pantalla de entrada y servicios de `usuarios`

- [x] 10.1 frontend-expert: `frontend/shell/src/services/usuarios.api.ts` — `registrar(payload)`, `login(email, password)`
- [x] 10.2 qa-expert (Red): tests RTL de `EntradaPage` — muestra las 3 opciones simétricas, navega al formulario correspondiente
- [x] 10.3 frontend-expert (Green): `frontend/shell/src/pages/EntradaPage.tsx` reemplazando el punto de entrada actual

## 11. Frontend: Formularios de registro y login

- [x] 11.1 qa-expert (Red): tests RTL de `RegistroPropietarioPage`/`RegistroInquilinoPage` — envío exitoso guarda sesión y redirige
- [x] 11.2 frontend-expert (Green): implementar ambas páginas (pueden compartir un único componente parametrizado por rol)
- [x] 11.3 qa-expert (Red): tests RTL de `RegistroAgentePage` — tras registro exitoso, muestra el paso de agencia (crear vs. buscar y unirse)
- [x] 11.4 frontend-expert (Green): `RegistroAgentePage` — tras recibir el JWT, encadena `POST /agencias/` o el flujo de búsqueda + `POST /agencias/{id}/solicitudes` (reutilizando `agencias.api.ts` de `inmuebles-app` o duplicando el cliente mínimo necesario en `shell`, a criterio de frontend-expert)
- [x] 11.5 qa-expert (Red): tests RTL de `LoginPage` — éxito guarda sesión y redirige, error muestra mensaje único
- [x] 11.6 frontend-expert (Green): `LoginPage.tsx`
- [x] 11.7 frontend-expert: eliminar `TokenLoginPage` y actualizar el router del `shell` para usar `EntradaPage`/`LoginPage` como punto de entrada sin sesión

## 12. Frontend: Testing E2E con Playwright MCP (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 12.1 Asegurar que `docker compose up` esté corriendo (shell, inmuebles-app, backend, postgres)
- [x] 12.2 E2E: registro completo como propietario → sesión activa → navega a `inmuebles-app` sin volver a loguearse
- [x] 12.3 E2E: registro completo como agente creando agencia nueva → verificar membresía y acceso a `InmueblesGestionadosPage`
- [x] 12.4 E2E: registro completo como agente buscando y solicitando unirse a una agencia existente → verificar estado `pendiente`
- [x] 12.5 E2E: login con credenciales inválidas → verificar mensaje de error único en la UI
- [x] 12.6 E2E: verificar que la búsqueda pública de inmuebles (HU-003, si ya implementada) sigue accesible sin sesión — no aplica, HU-003 no implementada todavía
- [x] 12.7 Restaurar el estado de la base de datos (eliminar usuarios/agencias de prueba creados durante el E2E)
- [x] 12.8 Documentar los escenarios y resultados en `openspec/changes/hu-008/specs/reports/YYYY-MM-DD-step-12-e2e-playwright.md`

## 13. Documentación (OBLIGATORIO)

- [x] 13.1 Actualizar `docs/architecture/architecture.md` con el árbol de `backend/usuarios/`, el nuevo endpoint `GET /agencias/buscar`, y las páginas nuevas del `shell`
- [x] 13.2 Marcar los criterios de aceptación cumplidos en `docs/user-stories/HU-008-registro-y-autenticacion.md`
