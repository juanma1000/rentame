# Reporte Paso 5 - Unit Tests y Verificación de Base de Datos

- Fecha: 2026-08-22
- Cambio: hu-003
- Agente: Claude Code (orquestando qa-expert/backend-expert)

## Comandos Ejecutados
- `docker compose exec backend pytest tests/inmuebles --no-cov -q`
- `docker compose exec backend pytest --no-cov -q`
- `docker compose exec -T postgres psql -U rentame -d rentame -c "select count(*) from inmueble;"` (baseline y post-test)

## Resultados de Unit Tests
- Tests focalizados (`inmuebles`): 81 passed, 0 failed.
- Suite completa del proyecto: 214 passed, 0 failed, 1 warning (deprecación de FastAPI preexistente, no relacionada).
- Duración: ~2.7s (focalizados), ~12s (suite completa).
- Notas: sin tests flaky ni reintentos. Se detectó y corrigió durante Red un choque de rutas de Starlette (`GET /inmuebles/publicos` matcheaba el template `/inmuebles/{inmueble_id}` con método distinto → 405 en vez de 404) — resuelto declarando las rutas públicas literales antes de las parametrizadas en `router.py`.

## Verificación de Estado de Base de Datos
- Baseline pre-test (`inmueble`): 4 filas.
- Post-test (`inmueble`): 4 filas (sin cambio).
- Estado restaurado: Sí — los tests corren contra `rentame_test` con rollback por test (fixture `db_session`), la base de desarrollo (`rentame`) no se toca.

## Resultado
- Estado del Paso 5: PASS
- Issues bloqueantes: ninguno
