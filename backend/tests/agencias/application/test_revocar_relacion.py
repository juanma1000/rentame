"""Unit tests for the `revocar_relacion` use case
(`agencias/application/revocar_relacion.py`).

Covers tasks 3.14-3.16 of `openspec/changes/hu-007/tasks.md`: the
"Revocación de la relación agencia-propietario por el propietario"
requirement of `openspec/changes/hu-007/specs/agencias/spec.md`, and the
"Despublicación en cascada por revocación de agencia" requirement of
`openspec/changes/hu-007/specs/inmuebles/spec.md`.

TDD Red phase: `agencias/application/revocar_relacion.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.6). This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `RevocarRelacionCommand`: a plain dataclass with `relacion_id: UUID`,
  `propietario_id: UUID` (the propietario revoking, no agencia approval
  needed per spec.md).
- `revocar_relacion(command, *, relacion_repository, usuario_repository,
  inmueble_repository, listar_mis_inmuebles=<real fn>,
  cambiar_disponibilidad=<real fn>) -> RelacionAgenciaPropietario`: an async
  function that:
  1. Raises `RelacionNoEncontrada` when `command.relacion_id` does not
     exist.
  2. Calls `.revocar()` on the relación (`ACTIVA -> REVOCADA`) and persists
     it via `relacion_repository.actualizar` — no agencia-side approval is
     required.
  3. Runs the despublicación cascade (design.md decisión 4), same mechanism
     as `confirmar_relacion`'s auto-revoke branch: resolves the revoked
     agencia's members via
     `usuario_repository.listar_ids_por_agencia(relacion.agencia_id)`, lists
     the propietario's inmuebles via
     `listar_mis_inmuebles(ListarMisInmueblesCommand(propietario_id=...),
     repository=inmueble_repository)`, and for every inmueble whose
     `agente_id` is in that member set calls
     `cambiar_disponibilidad(CambiarDisponibilidadCommand(inmueble_id=...,
     nuevo_estado=EstadoInmueble.OCULTO, propietario_id=None),
     repository=inmueble_repository)`. Inmuebles with `agente_id=None` (the
     propietario's own direct publications), or managed by an agente outside
     that set, are NOT touched.

`listar_mis_inmuebles`/`cambiar_disponibilidad` are received as named
keyword parameters (not imported and called directly) — same rationale as
`confirmar_relacion`, see `tests/agencias/application/conftest.py`.
"""

import uuid
from decimal import Decimal

import pytest

from agencias.application.revocar_relacion import RevocarRelacionCommand, revocar_relacion
from agencias.domain.exceptions import PropietarioInvalido
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
    """See the identically-named helper in `test_confirmar_relacion.py` for
    the rationale of stamping `agente_id` post-construction."""
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


class TestRevocarRelacionSinAprobacionDeAgencia:
    async def test_should_revoke_active_relacion_without_agencia_approval(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
        spy_listar_mis_inmuebles: SpyListarMisInmuebles,
        spy_cambiar_disponibilidad: SpyCambiarDisponibilidad,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=propietario_id
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        # Act
        assert relacion.id is not None
        result = await revocar_relacion(
            RevocarRelacionCommand(relacion_id=relacion.id, propietario_id=propietario_id),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
            inmueble_repository=None,
            listar_mis_inmuebles=spy_listar_mis_inmuebles,
            cambiar_disponibilidad=spy_cambiar_disponibilidad,
        )

        # Assert
        assert result.estado == EstadoRelacion.REVOCADA
        assert relacion in fake_relacion_repository.actualizar_calls


class TestRevocarRelacionRejectsNonOwnerPropietario:
    async def test_should_raise_propietario_invalido_when_caller_is_not_the_owner(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
        spy_listar_mis_inmuebles: SpyListarMisInmuebles,
        spy_cambiar_disponibilidad: SpyCambiarDisponibilidad,
    ) -> None:
        # Arrange: relación belongs to `propietario_id`, but a different
        # propietario (`otro_propietario_id`) attempts to revoke it.
        agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        otro_propietario_id = uuid.uuid4()
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=propietario_id
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        # Act / Assert
        assert relacion.id is not None
        with pytest.raises(PropietarioInvalido):
            await revocar_relacion(
                RevocarRelacionCommand(relacion_id=relacion.id, propietario_id=otro_propietario_id),
                relacion_repository=fake_relacion_repository,
                usuario_repository=fake_usuario_repository,
                inmueble_repository=None,
                listar_mis_inmuebles=spy_listar_mis_inmuebles,
                cambiar_disponibilidad=spy_cambiar_disponibilidad,
            )

        # Assert: the relación's estado is unchanged and no persistence/cascade
        # side effects were triggered.
        assert relacion.estado == EstadoRelacion.ACTIVA
        assert fake_relacion_repository.actualizar_calls == []
        assert spy_cambiar_disponibilidad.calls == []


class TestRevocarRelacionDisparaCascadaSoloParaAgentesDeLaAgencia:
    async def test_should_despublish_only_inmuebles_managed_by_agencia_agentes(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
        spy_listar_mis_inmuebles: SpyListarMisInmuebles,
        spy_cambiar_disponibilidad: SpyCambiarDisponibilidad,
    ) -> None:
        # Arrange
        agencia_revocada_id = uuid.uuid4()
        otra_agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        agente_de_la_agencia_id = uuid.uuid4()
        agente_de_otra_agencia_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_de_la_agencia_id, agencia_revocada_id)
        fake_usuario_repository.seed(agente_de_otra_agencia_id, otra_agencia_id)

        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_revocada_id, propietario_id=propietario_id
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        inmueble_de_la_agencia = _build_inmueble(
            propietario_id=propietario_id, agente_id=agente_de_la_agencia_id
        )
        inmueble_de_otra_agencia = _build_inmueble(
            propietario_id=propietario_id, agente_id=agente_de_otra_agencia_id
        )
        inmueble_sin_agente = _build_inmueble(propietario_id=propietario_id, agente_id=None)
        spy_listar_mis_inmuebles.inmuebles_por_propietario[propietario_id] = [
            inmueble_de_la_agencia,
            inmueble_de_otra_agencia,
            inmueble_sin_agente,
        ]

        # Act
        assert relacion.id is not None
        await revocar_relacion(
            RevocarRelacionCommand(relacion_id=relacion.id, propietario_id=propietario_id),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
            inmueble_repository=None,
            listar_mis_inmuebles=spy_listar_mis_inmuebles,
            cambiar_disponibilidad=spy_cambiar_disponibilidad,
        )

        # Assert: exactly one call, only for the inmueble managed by an
        # agente of the revoked agencia.
        assert spy_cambiar_disponibilidad.calls == [
            CambiarDisponibilidadCommand(
                inmueble_id=inmueble_de_la_agencia.id,
                nuevo_estado=EstadoInmueble.OCULTO,
                propietario_id=None,
            )
        ]


class TestRevocarRelacionNoDespublicaInmueblesSinAgente:
    async def test_should_not_call_cambiar_disponibilidad_for_inmuebles_without_agente(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
        spy_listar_mis_inmuebles: SpyListarMisInmuebles,
        spy_cambiar_disponibilidad: SpyCambiarDisponibilidad,
    ) -> None:
        # Arrange: propietario has exactly one inmueble, published directly
        # (no agente), plus an active relación with an agencia.
        agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=propietario_id
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        inmueble_sin_agente = _build_inmueble(propietario_id=propietario_id, agente_id=None)
        spy_listar_mis_inmuebles.inmuebles_por_propietario[propietario_id] = [inmueble_sin_agente]

        # Act
        assert relacion.id is not None
        await revocar_relacion(
            RevocarRelacionCommand(relacion_id=relacion.id, propietario_id=propietario_id),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
            inmueble_repository=None,
            listar_mis_inmuebles=spy_listar_mis_inmuebles,
            cambiar_disponibilidad=spy_cambiar_disponibilidad,
        )

        # Assert
        assert spy_cambiar_disponibilidad.calls == []
