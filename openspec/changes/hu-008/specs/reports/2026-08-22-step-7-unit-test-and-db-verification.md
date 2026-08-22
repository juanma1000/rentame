# Reporte Paso 7 - Unit Tests y Verificación de Base de Datos

- Fecha: 2026-08-22
- Cambio: hu-008
- Agente: Claude Code (orquestando qa-expert/backend-expert)

## Comandos Ejecutados
- `docker compose exec backend pytest tests/usuarios tests/agencias --no-cov -v`
- `docker compose exec backend pytest --no-cov -q`
- `docker compose exec -T postgres psql -U rentame -d rentame -c "select count(*) from usuario/agencia/inmueble;"` (baseline y post-test)

## Resultados de Unit Tests
- Tests focalizados (`usuarios` + `agencias`): 110 passed, 0 failed, 0 skipped.
- Suite completa del proyecto: 199 passed, 0 failed, 1 warning (deprecación de `HTTP_422_UNPROCESSABLE_ENTITY` en FastAPI, preexistente, no relacionada a este change).
- Duración: ~9.7s (focalizados), ~11.6s (suite completa).
- Notas: durante la implementación se encontró y corrigió un problema real — la tabla `usuario` de la base de datos de test (`rentame_test`) tenía esquema desactualizado (creada antes de agregar `password_hash`/`nombre` al modelo; `Base.metadata.create_all` no altera tablas existentes). Se corrigió con `ALTER TABLE usuario ADD COLUMN password_hash ...` / `ADD COLUMN nombre ...` directamente sobre `rentame_test`. Sin este fix, 62 tests de integración fallaban con `UndefinedColumnError`. No hubo tests flaky ni reintentos.

## Verificación de Estado de Base de Datos
- Baseline pre-test (base de datos de desarrollo `rentame`, no tocada por los tests — que corren contra `rentame_test` con rollback por test):
  - `usuario`: 8 filas
  - `agencia`: 1 fila
  - `inmueble`: 4 filas
- Validación post-test:
  - `usuario`: 8 filas (sin cambio)
  - `agencia`: 1 fila (sin cambio)
  - `inmueble`: 4 filas (sin cambio)
- Estado restaurado: Sí (no hubo mutación alguna — la fixture `db_session` de `backend/tests/conftest.py` hace `rollback()` después de cada test, y los tests corren contra `rentame_test`, base de datos separada de `rentame`).

## Resultado
- Estado del Paso 7: PASS
- Issues bloqueantes: ninguno. Issue no bloqueante resuelto durante la ejecución: esquema desactualizado de `rentame_test` (ver nota arriba) — corregido antes de considerar este paso completo.
