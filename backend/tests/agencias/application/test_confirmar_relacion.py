"""Unit tests for the `confirmar_relacion` use case
(`agencias/application/confirmar_relacion.py`).

Covers tasks 3.11-3.13 of `openspec/changes/hu-007/tasks.md`: the "Relación
agencia-propietario iniciada por el propietario" and "Máximo una agencia
activa por propietario" requirements of
`openspec/changes/hu-007/specs/agencias/spec.md`, and the "Despublicación en
cascada por revocación de agencia" requirement of
`openspec/changes/hu-007/specs/inmuebles/spec.md`.

TDD Red phase: `agencias/application/confirmar_relacion.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.5). This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `ConfirmarRelacionCommand`: a plain dataclass with `relacion_id: UUID`,
  `agente_id: UUID` (the agente performing the confirmation).
- `confirmar_relacion(command, *, relacion_repository, usuario_repository,
  inmueble_repository, listar_mis_inmuebles=<real fn>,
  cambiar_disponibilidad=<real fn>) -> RelacionAgenciaPropietario`: an async
  function that:
  1. Raises `RelacionNoEncontrada` when `command.relacion_id` does not
     exist.
  2. Raises `AgenteNoEsMiembroDeAgencia` when
     `usuario_repository.obtener_agencia_id(command.agente_id)` does not
     equal the relación's `agencia_id` — without mutating anything and
     without calling `listar_mis_inmuebles`/`cambiar_disponibilidad`.
  3. Looks up `relacion_repository.obtener_activa_por_propietario(propietario_id)`.
     If it returns another relación (design.md decisión 3, auto-revocación):
     a. Calls `.revocar()` on it and persists via
        `relacion_repository.actualizar`.
     b. Runs the despublicación cascade (design.md decisión 4): resolves the
        revoked agencia's members via
        `usuario_repository.listar_ids_por_agencia(agencia_revocada_id)`,
        lists the propietario's inmuebles via
        `listar_mis_inmuebles(ListarMisInmueblesCommand(propietario_id=...),
        repository=inmueble_repository)`, and for every inmueble whose
        `agente_id` is in that member set calls
        `cambiar_disponibilidad(CambiarDisponibilidadCommand(inmueble_id=...,
        nuevo_estado=EstadoInmueble.OCULTO, propietario_id=None),
        repository=inmueble_repository)`. Inmuebles with `agente_id=None`,
        or managed by an agente outside that set, are NOT touched.
  4. Calls `.activar()` on the relación being confirmed and persists it via
     `relacion_repository.actualizar`.

`listar_mis_inmuebles`/`cambiar_disponibilidad` are received as named
keyword parameters (not imported and called directly), precisely so tests
can substitute `SpyListarMisInmuebles`/`SpyCambiarDisponibilidad` — see
`tests/agencias/application/conftest.py`.
"""

import uuid
from decimal import Decimal

import pytest

from agencias.application.confirmar_relacion import ConfirmarRelacionCommand, confirmar_relacion
from agencias.domain.exceptions import AgenteNoEsMiembroDeAgencia
from agencias.domain.relacion_agencia_propietario import (
    EstadoRelacion,
    RelacionAgenciaPropietario,
)
from inmuebles.application.cambiar_disponibilidad import CambiarDisponibilidadCommand
from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from tests.agencias.application.conftest import (
    FakeRelacionRepository,
    FakeUsuarioAgenciaRepository,
    SpyCambiarDisponibilidad,
    SpyListarMisInmuebles,
)


def _build_inmueble(*, propietario_id: uuid.UUID, agente_id: uuid.UUID | None) -> Inmueble:
    """Build an `Inmueble` (via the real domain factory) and stamp
    `agente_id` on it directly afterwards.

    NOTE for `backend-expert`: `Inmueble` (`inmuebles/domain/inmueble.py`)
    does not declare an `agente_id` field yet (per `design.md`'s Context:
    the ORM column exists since HU-001, but `Inmueble.crear` never accepted
    it). Design.md decisión 4 requires filtering returned inmuebles by
    `agente_id` inside the `agencias` use case, so this is a prerequisite
    gap: `Inmueble` needs an `agente_id: uuid.UUID | None = None` field
    (populated by the repository mapping, never accepted as a `crear(...)`
    argument, consistent with the HU-002 non-goal). This helper stamps the
    attribute directly (works today because `Inmueble` is a plain,
    non-`slots` dataclass) purely so these Red tests can build fixtures
    without requiring that field to exist yet.
    """
    inmueble = Inmueble.crear(
        propietario_id=propietario_id,
        direccion="Calle 10 # 20-30",
        barrio="El Poblado",
        ciudad="Medellin",
        tipo="apartamento",
        area_m2=Decimal("65.5"),
        habitaciones=2,
        banos=2,
        valor_mensual=Decimal("1500000"),
        descripcion="Apartamento amoblado cerca al metro",
        fotos=[
            FotoInmueble(
                url_storage="https://storage.example.com/inmuebles/fotos/1.jpg",
                storage_key="inmuebles/fotos/1.jpg",
                orden=1,
                es_principal=True,
            )
        ],
    )
    inmueble.id = uuid.uuid4()
    inmueble.agente_id = agente_id  # type: ignore[attr-defined]
    return inmueble


class TestConfirmarRelacionSinPrevia:
    async def test_should_activate_relacion_when_no_previous_active_relacion_exists(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
        spy_listar_mis_inmuebles: SpyListarMisInmuebles,
        spy_cambiar_disponibilidad: SpyCambiarDisponibilidad,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        agente_confirmador_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_confirmador_id, agencia_id)
        relacion = fake_relacion_repository.seed(
            RelacionAgenciaPropietario.crear(agencia_id=agencia_id, propietario_id=propietario_id)
        )

        # Act
        assert relacion.id is not None
        result = await confirmar_relacion(
            ConfirmarRelacionCommand(relacion_id=relacion.id, agente_id=agente_confirmador_id),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
            inmueble_repository=None,
            listar_mis_inmuebles=spy_listar_mis_inmuebles,
            cambiar_disponibilidad=spy_cambiar_disponibilidad,
        )

        # Assert
        assert result.estado == EstadoRelacion.ACTIVA
        assert spy_listar_mis_inmuebles.calls == []
        assert spy_cambiar_disponibilidad.calls == []


class TestConfirmarRelacionConPreviaActiva:
    async def test_should_auto_revoke_previous_active_relacion_and_trigger_cascade(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
        spy_listar_mis_inmuebles: SpyListarMisInmuebles,
        spy_cambiar_disponibilidad: SpyCambiarDisponibilidad,
    ) -> None:
        # Arrange: propietario has an ACTIVA relación with agencia A, and a
        # PENDIENTE relación with agencia B about to be confirmed.
        agencia_a_id = uuid.uuid4()
        agencia_b_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        agente_a_id = uuid.uuid4()  # sole member of agencia A
        agente_b_id = uuid.uuid4()  # confirms on behalf of agencia B
        fake_usuario_repository.seed(agente_a_id, agencia_a_id)
        fake_usuario_repository.seed(agente_b_id, agencia_b_id)

        relacion_a = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_a_id, propietario_id=propietario_id
        )
        relacion_a.activar()
        fake_relacion_repository.seed(relacion_a)

        relacion_b = fake_relacion_repository.seed(
            RelacionAgenciaPropietario.crear(agencia_id=agencia_b_id, propietario_id=propietario_id)
        )

        inmueble_gestionado_por_a = _build_inmueble(
            propietario_id=propietario_id, agente_id=agente_a_id
        )
        inmueble_sin_agente = _build_inmueble(propietario_id=propietario_id, agente_id=None)
        spy_listar_mis_inmuebles.inmuebles_por_propietario[propietario_id] = [
            inmueble_gestionado_por_a,
            inmueble_sin_agente,
        ]

        # Act
        assert relacion_b.id is not None
        result = await confirmar_relacion(
            ConfirmarRelacionCommand(relacion_id=relacion_b.id, agente_id=agente_b_id),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
            inmueble_repository=None,
            listar_mis_inmuebles=spy_listar_mis_inmuebles,
            cambiar_disponibilidad=spy_cambiar_disponibilidad,
        )

        # Assert: relacion_b is now active, relacion_a was auto-revoked.
        assert result.estado == EstadoRelacion.ACTIVA
        assert relacion_a.estado == EstadoRelacion.REVOCADA
        assert relacion_a in fake_relacion_repository.actualizar_calls

        # Assert: cascade queried the right propietario and hit exactly the
        # inmueble managed by an agencia-A agente.
        assert len(spy_listar_mis_inmuebles.calls) == 1
        assert spy_listar_mis_inmuebles.calls[0].propietario_id == propietario_id

        assert spy_cambiar_disponibilidad.calls == [
            CambiarDisponibilidadCommand(
                inmueble_id=inmueble_gestionado_por_a.id,
                nuevo_estado=EstadoInmueble.OCULTO,
                propietario_id=None,
            )
        ]


class TestConfirmarRelacionRejectsNonMemberConfirmer:
    async def test_should_raise_agente_no_es_miembro_when_confirmer_is_not_agencia_member(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
        spy_listar_mis_inmuebles: SpyListarMisInmuebles,
        spy_cambiar_disponibilidad: SpyCambiarDisponibilidad,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        otra_agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        agente_no_miembro_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_no_miembro_id, otra_agencia_id)
        relacion = fake_relacion_repository.seed(
            RelacionAgenciaPropietario.crear(agencia_id=agencia_id, propietario_id=propietario_id)
        )

        # Act / Assert
        assert relacion.id is not None
        with pytest.raises(AgenteNoEsMiembroDeAgencia):
            await confirmar_relacion(
                ConfirmarRelacionCommand(relacion_id=relacion.id, agente_id=agente_no_miembro_id),
                relacion_repository=fake_relacion_repository,
                usuario_repository=fake_usuario_repository,
                inmueble_repository=None,
                listar_mis_inmuebles=spy_listar_mis_inmuebles,
                cambiar_disponibilidad=spy_cambiar_disponibilidad,
            )

        assert relacion.estado == EstadoRelacion.PENDIENTE
        assert fake_relacion_repository.actualizar_calls == []
        assert spy_listar_mis_inmuebles.calls == []
        assert spy_cambiar_disponibilidad.calls == []
