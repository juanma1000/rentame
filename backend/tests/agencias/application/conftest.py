"""In-memory fakes for the `agencias` outbound ports
(`agencias/domain/ports.py`) and for the `inmuebles.application` functions
that the despublicación-cascade use cases (`confirmar_relacion`,
`revocar_relacion`) call as injected, named dependencies (per
`openspec/changes/hu-007/design.md` decisión 4 and the task delegation for
tasks 3.11-3.16).

These fakes are test doubles only — no production code lives here. Same
pattern as `tests/inmuebles/application/conftest.py` from HU-001: fakes
satisfy the `Protocol`s structurally (no inheritance needed).

Mechanism for "qué agentes pertenecen a esta agencia" (design.md decisión 4,
step 1): `UsuarioAgenciaRepositoryPort.listar_ids_por_agencia(agencia_id)`,
backed in production by `usuario.agencia_id` (design.md decisión 2). It is
also reused by `salir_de_agencia` (tasks 3.7-3.9) to know whether the acting
agente is the last member of their agencia.

Fixing the "fake `inmuebles`" contract for tasks 3.11-3.16: `confirmar_relacion`
and `revocar_relacion` never import `inmuebles.application.listar_mis_inmuebles`
/`cambiar_disponibilidad` directly. Instead, they receive them as named
keyword parameters (defaulting, in production, to the real functions), so
tests can pass spy/fake callables instead — see `SpyListarMisInmuebles`/
`SpyCambiarDisponibilidad` below. Both spies match the exact async call
signature of the real functions: `(command, *, repository) -> ...`, so the
agencias use case must also receive (and forward) an `inmueble_repository`
even though these tests never exercise a real one (a `None`/sentinel value
is enough, since the spies ignore it).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import (
    EstadoRelacion,
    RelacionAgenciaPropietario,
)
from agencias.domain.solicitud_ingreso import SolicitudIngreso
from inmuebles.application.cambiar_disponibilidad import CambiarDisponibilidadCommand
from inmuebles.application.listar_mis_inmuebles import ListarMisInmueblesCommand
from inmuebles.domain.inmueble import Inmueble


@dataclass
class FakeAgenciaRepository:
    """In-memory stand-in for `AgenciaRepositoryPort`."""

    _agencias: dict[UUID, Agencia] = field(default_factory=dict)
    guardar_calls: list[Agencia] = field(default_factory=list)
    actualizar_calls: list[Agencia] = field(default_factory=list)

    def seed(self, agencia: Agencia) -> Agencia:
        if agencia.id is None:
            agencia.id = uuid4()
        self._agencias[agencia.id] = agencia
        return agencia

    async def guardar(self, agencia: Agencia) -> Agencia:
        self.guardar_calls.append(agencia)
        agencia.id = uuid4()
        self._agencias[agencia.id] = agencia
        return agencia

    async def actualizar(self, agencia: Agencia) -> Agencia:
        self.actualizar_calls.append(agencia)
        assert agencia.id is not None, "actualizar() called with an Agencia that has no id"
        self._agencias[agencia.id] = agencia
        return agencia

    async def obtener_por_id(self, agencia_id: UUID) -> Agencia | None:
        return self._agencias.get(agencia_id)

    async def buscar(self, texto: str) -> list[Agencia]:
        """Case-insensitive substring match on `razon_social`/`nit`, added
        for HU-008's `buscar_agencias` use case
        (`openspec/changes/hu-008/design.md` decisión 4).
        """
        texto_lower = texto.lower()
        return [
            agencia
            for agencia in self._agencias.values()
            if texto_lower in agencia.razon_social.lower() or texto_lower in agencia.nit.lower()
        ]


@dataclass
class FakeRelacionRepository:
    """In-memory stand-in for `RelacionRepositoryPort`."""

    _relaciones: dict[UUID, RelacionAgenciaPropietario] = field(default_factory=dict)
    guardar_calls: list[RelacionAgenciaPropietario] = field(default_factory=list)
    actualizar_calls: list[RelacionAgenciaPropietario] = field(default_factory=list)

    def seed(self, relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietario:
        if relacion.id is None:
            relacion.id = uuid4()
        self._relaciones[relacion.id] = relacion
        return relacion

    async def guardar(self, relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietario:
        self.guardar_calls.append(relacion)
        relacion.id = uuid4()
        self._relaciones[relacion.id] = relacion
        return relacion

    async def actualizar(self, relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietario:
        self.actualizar_calls.append(relacion)
        assert relacion.id is not None, "actualizar() called with a relacion that has no id"
        self._relaciones[relacion.id] = relacion
        return relacion

    async def obtener_por_id(self, relacion_id: UUID) -> RelacionAgenciaPropietario | None:
        return self._relaciones.get(relacion_id)

    async def obtener_activa_por_propietario(
        self, propietario_id: UUID
    ) -> RelacionAgenciaPropietario | None:
        for relacion in self._relaciones.values():
            if (
                relacion.propietario_id == propietario_id
                and relacion.estado == EstadoRelacion.ACTIVA
            ):
                return relacion
        return None

    async def listar_por_agencia(self, agencia_id: UUID) -> list[RelacionAgenciaPropietario]:
        return [r for r in self._relaciones.values() if r.agencia_id == agencia_id]


@dataclass
class FakeSolicitudIngresoRepository:
    """In-memory stand-in for `SolicitudIngresoRepositoryPort`."""

    _solicitudes: dict[UUID, SolicitudIngreso] = field(default_factory=dict)
    guardar_calls: list[SolicitudIngreso] = field(default_factory=list)
    actualizar_calls: list[SolicitudIngreso] = field(default_factory=list)

    def seed(self, solicitud: SolicitudIngreso) -> SolicitudIngreso:
        if solicitud.id is None:
            solicitud.id = uuid4()
        self._solicitudes[solicitud.id] = solicitud
        return solicitud

    async def guardar(self, solicitud: SolicitudIngreso) -> SolicitudIngreso:
        self.guardar_calls.append(solicitud)
        solicitud.id = uuid4()
        self._solicitudes[solicitud.id] = solicitud
        return solicitud

    async def actualizar(self, solicitud: SolicitudIngreso) -> SolicitudIngreso:
        self.actualizar_calls.append(solicitud)
        assert solicitud.id is not None, "actualizar() called with a solicitud that has no id"
        self._solicitudes[solicitud.id] = solicitud
        return solicitud

    async def obtener_por_id(self, solicitud_id: UUID) -> SolicitudIngreso | None:
        return self._solicitudes.get(solicitud_id)


@dataclass
class FakeUsuarioAgenciaRepository:
    """In-memory stand-in for `UsuarioAgenciaRepositoryPort`.

    Backs the `usuario.agencia_id` pointer (design.md decisión 2) with a
    plain `dict[usuario_id, agencia_id | None]`, seeded directly by tests.
    """

    _agencia_por_usuario: dict[UUID, UUID | None] = field(default_factory=dict)
    asignar_calls: list[tuple[UUID, UUID]] = field(default_factory=list)
    remover_calls: list[UUID] = field(default_factory=list)

    def seed(self, usuario_id: UUID, agencia_id: UUID | None) -> None:
        self._agencia_por_usuario[usuario_id] = agencia_id

    async def obtener_agencia_id(self, usuario_id: UUID) -> UUID | None:
        return self._agencia_por_usuario.get(usuario_id)

    async def asignar_agencia(self, usuario_id: UUID, agencia_id: UUID) -> None:
        self.asignar_calls.append((usuario_id, agencia_id))
        self._agencia_por_usuario[usuario_id] = agencia_id

    async def remover_agencia(self, usuario_id: UUID) -> None:
        self.remover_calls.append(usuario_id)
        self._agencia_por_usuario[usuario_id] = None

    async def listar_ids_por_agencia(self, agencia_id: UUID) -> list[UUID]:
        return [
            usuario_id
            for usuario_id, a_id in self._agencia_por_usuario.items()
            if a_id == agencia_id
        ]


@dataclass
class SpyListarMisInmuebles:
    """Fake for the injected `listar_mis_inmuebles` dependency.

    Matches the real function's signature exactly
    (`inmuebles.application.listar_mis_inmuebles.listar_mis_inmuebles`):
    `async def (command: ListarMisInmueblesCommand, *, repository) -> list[Inmueble]`.
    Seed `inmuebles_por_propietario` with what the fake should return for a
    given `propietario_id`; `calls` records every `command` received so
    tests can assert on `propietario_id` and on `repository` being forwarded
    unchanged.
    """

    inmuebles_por_propietario: dict[UUID, list[Inmueble]] = field(default_factory=dict)
    calls: list[ListarMisInmueblesCommand] = field(default_factory=list)
    repository_calls: list[object] = field(default_factory=list)

    async def __call__(
        self, command: ListarMisInmueblesCommand, *, repository: object
    ) -> list[Inmueble]:
        self.calls.append(command)
        self.repository_calls.append(repository)
        return self.inmuebles_por_propietario.get(command.propietario_id, [])


@dataclass
class SpyCambiarDisponibilidad:
    """Fake for the injected `cambiar_disponibilidad` dependency.

    Matches the real function's signature exactly
    (`inmuebles.application.cambiar_disponibilidad.cambiar_disponibilidad`):
    `async def (command: CambiarDisponibilidadCommand, *, repository) -> Inmueble`.
    `calls` records every `command` received, so tests can assert the exact
    `inmueble_id`/`nuevo_estado`/`propietario_id` triple invoked by the
    cascade — the core assertion of tasks 3.12, 3.15, 3.16.
    """

    calls: list[CambiarDisponibilidadCommand] = field(default_factory=list)
    repository_calls: list[object] = field(default_factory=list)

    async def __call__(
        self, command: CambiarDisponibilidadCommand, *, repository: object
    ) -> Inmueble | None:
        self.calls.append(command)
        self.repository_calls.append(repository)
        return None


@pytest.fixture
def fake_agencia_repository() -> FakeAgenciaRepository:
    return FakeAgenciaRepository()


@pytest.fixture
def fake_relacion_repository() -> FakeRelacionRepository:
    return FakeRelacionRepository()


@pytest.fixture
def fake_solicitud_repository() -> FakeSolicitudIngresoRepository:
    return FakeSolicitudIngresoRepository()


@pytest.fixture
def fake_usuario_repository() -> FakeUsuarioAgenciaRepository:
    return FakeUsuarioAgenciaRepository()


@pytest.fixture
def spy_listar_mis_inmuebles() -> SpyListarMisInmuebles:
    return SpyListarMisInmuebles()


@pytest.fixture
def spy_cambiar_disponibilidad() -> SpyCambiarDisponibilidad:
    return SpyCambiarDisponibilidad()
