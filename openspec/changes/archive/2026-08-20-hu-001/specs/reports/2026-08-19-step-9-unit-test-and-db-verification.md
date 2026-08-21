# Reporte Paso 9 - Unit Tests y Verificación de Base de Datos

- Fecha: 2026-08-19
- Cambio: hu-001
- Agente: qa-expert

## Comandos Ejecutados
- `python -m pytest tests/shared/ -v` (Grupo 8: confirmación de tests preexistentes)
- `python -m pytest tests/inmuebles/ -v --no-cov` (9.2: tests focalizados del dominio `inmuebles`)
- `python -m pytest --cov=shared --cov=usuarios --cov=inmuebles --cov-report=term-missing --cov-fail-under=80` (9.3: suite completa con cobertura)
- `docker exec rentame-postgres psql -U rentame -d rentame -c "SELECT (SELECT count(*) FROM inmueble) ..., (SELECT count(*) FROM foto_inmueble) ..., (SELECT count(*) FROM usuario) ...;"` (baseline y validación post-test sobre la DB de desarrollo `rentame`)
- `docker exec rentame-postgres psql -U rentame -d rentame -c "SELECT id, email, rol FROM usuario ORDER BY email;"` (baseline y validación post-test de filas de `usuario`)
- `alembic current` (confirmación de que la DB de desarrollo está en el head de migraciones esperado)

## Resultados de Unit Tests
- Tests preexistentes (`tests/shared/`, Grupo 8): 11 passed, 0 failed, 0 skipped
- Tests focalizados (`tests/inmuebles/`, dominio + casos de uso + infraestructura): 44 passed, 0 failed, 0 skipped
- Suite completa/requerida (`pytest` con `--cov-fail-under=80` sobre `shared`, `usuarios`, `inmuebles`): 55 passed, 0 failed, 0 skipped
- Duración: 1.33s (suite completa)
- Notas: no se observó comportamiento flaky ni reintentos. Los `DeprecationWarning` de `asyncio.get_event_loop_policy` provienen de `pytest-asyncio` en Python 3.14 y no afectan el resultado de los tests (no bloqueante, fuera del alcance de este change).

### Cobertura — módulos de lógica de negocio nueva (`inmuebles`)
| Módulo | Cover |
|---|---|
| `inmuebles/domain/inmueble.py` | 100% |
| `inmuebles/domain/foto.py` | 100% |
| `inmuebles/domain/exceptions.py` | 100% |
| `inmuebles/domain/ports.py` | 100% |
| `inmuebles/application/publicar_inmueble.py` | 100% |
| `inmuebles/application/editar_inmueble.py` | 100% |
| `inmuebles/application/cambiar_disponibilidad.py` | 100% |
| `inmuebles/application/listar_mis_inmuebles.py` | 100% |

Cobertura total del proyecto (`shared` + `usuarios` + `inmuebles`): **98.34%** (449 statements, 5 miss; 34 branches, 3 partial). Umbral mínimo exigido por `openspec/config.yaml`: 80%. Ambos módulos de lógica de negocio nueva (`inmuebles/domain` e `inmuebles/application`) están al 100%, muy por encima del mínimo.

Nota informativa (no bloqueante): dos módulos de infraestructura quedan levemente por debajo del 100% — `inmuebles/infrastructure/api/schemas.py` (96%, línea 71 sin cubrir) e `inmuebles/infrastructure/persistence/repository.py` (93%, líneas 38 y 44 sin cubrir). No son lógica de negocio de dominio/aplicación (no aplican al umbral del 80% de esas capas específicas), pero se dejan señaladas para que `backend-expert` evalúe si ameritan un test adicional en una iteración futura.

## Verificación de Estado de Base de Datos
Se verificó la base de datos de **desarrollo** (`rentame`, no `rentame_test` — la de test usa rollback transaccional por test vía la fixture `db_session` de `tests/conftest.py`).

- Baseline pre-test:
  - `inmueble`: 0 filas
  - `foto_inmueble`: 0 filas
  - `usuario`: 0 filas
- Validación post-test:
  - `inmueble`: 0 filas
  - `foto_inmueble`: 0 filas
  - `usuario`: 0 filas
- Estado restaurado: Sí (no hubo mutación — el estado post-test es idéntico al baseline pre-test)
- Acciones de restauración (si aplica): Ninguna necesaria. `alembic current` confirma que la DB de desarrollo permanece en el head de migraciones (`8302335a8c95`), sin cambios de esquema.

## Resultado
- Estado del Paso 9: PASS
- Issues bloqueantes: ninguno
