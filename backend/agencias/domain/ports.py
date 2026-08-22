"""Outbound ports for the `agencias` domain.

These `Protocol`s are the interfaces the application layer (tasks 3.x of
`openspec/changes/hu-007/tasks.md`) depends on instead of depending on
concrete infrastructure. Concrete adapters are implemented in
`agencias/infrastructure/` in a later phase, per
`docs/architecture/architecture.md`'s hexagonal layout for this domain.

Methods are `async` because the project's persistence layer is built on
SQLAlchemy's async engine/session (see `shared/infrastructure/database.py`),
following the same pattern as `inmuebles/domain/ports.py`.

`Protocol` (structural typing) is used rather than `ABC`, same rationale as
`inmuebles/domain/ports.py`: adapters only need to match the shape, not
inherit from a common base.

Signatures here are not necessarily exhaustive yet — the next phase (use
cases, tasks 3.x) will complete/adjust them as needed.
"""

from typing import Protocol
from uuid import UUID

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import RelacionAgenciaPropietario
from agencias.domain.solicitud_ingreso import SolicitudIngreso


class AgenciaRepositoryPort(Protocol):
    """Persistence contract for the `Agencia` aggregate."""

    async def guardar(self, agencia: Agencia) -> Agencia:
        """Insert a new `Agencia` and return it with `id` set."""
        ...

    async def actualizar(self, agencia: Agencia) -> Agencia:
        """Persist changes to an existing `Agencia`."""
        ...

    async def obtener_por_id(self, agencia_id: UUID) -> Agencia | None:
        """Return the `Agencia` matching `agencia_id`, or `None` if it does not exist."""
        ...


class RelacionRepositoryPort(Protocol):
    """Persistence contract for the `RelacionAgenciaPropietario` aggregate."""

    async def guardar(self, relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietario:
        """Insert a new `RelacionAgenciaPropietario` and return it with `id` set."""
        ...

    async def actualizar(self, relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietario:
        """Persist changes to an existing `RelacionAgenciaPropietario`."""
        ...

    async def obtener_por_id(self, relacion_id: UUID) -> RelacionAgenciaPropietario | None:
        """Return the relación matching `relacion_id`, or `None` if it does not exist."""
        ...

    async def obtener_activa_por_propietario(
        self, propietario_id: UUID
    ) -> RelacionAgenciaPropietario | None:
        """Return the `ACTIVA` relación for `propietario_id`, or `None` if it has none."""
        ...

    async def listar_por_agencia(self, agencia_id: UUID) -> list[RelacionAgenciaPropietario]:
        """Return every relación belonging to `agencia_id` (empty list if none)."""
        ...


class SolicitudIngresoRepositoryPort(Protocol):
    """Persistence contract for the `SolicitudIngreso` aggregate."""

    async def guardar(self, solicitud: SolicitudIngreso) -> SolicitudIngreso:
        """Insert a new `SolicitudIngreso` and return it with `id` set."""
        ...

    async def actualizar(self, solicitud: SolicitudIngreso) -> SolicitudIngreso:
        """Persist changes to an existing `SolicitudIngreso`."""
        ...

    async def obtener_por_id(self, solicitud_id: UUID) -> SolicitudIngreso | None:
        """Return the solicitud matching `solicitud_id`, or `None` if it does not exist."""
        ...


class UsuarioAgenciaRepositoryPort(Protocol):
    """Persistence contract for the agente-agencia membership pointer.

    Per `design.md` decisión 2, membership is NOT a separate join table —
    it is the nullable `usuario.agencia_id` column (cardinalidad 1 agente :
    1 agencia). This port is how the `agencias` application layer (tasks 3.x
    of `openspec/changes/hu-007/tasks.md`) reads/writes that column without
    depending on `usuarios` infrastructure directly. A concrete adapter
    (`agencias/infrastructure/` or `usuarios/infrastructure/`, decided in a
    later phase) will back it with a real query against the `usuario` table.
    """

    async def obtener_agencia_id(self, usuario_id: UUID) -> UUID | None:
        """Return the `agencia_id` currently assigned to `usuario_id`, or
        `None` if that usuario (always an agente in practice) has none."""
        ...

    async def asignar_agencia(self, usuario_id: UUID, agencia_id: UUID) -> None:
        """Set `usuario.agencia_id = agencia_id` for `usuario_id`."""
        ...

    async def remover_agencia(self, usuario_id: UUID) -> None:
        """Set `usuario.agencia_id = NULL` for `usuario_id`."""
        ...

    async def listar_ids_por_agencia(self, agencia_id: UUID) -> list[UUID]:
        """Return the `usuario.id` of every agente whose `agencia_id` equals
        `agencia_id` (empty list if the agencia has no members). Used both by
        `salir_de_agencia` (task 3.7-3.9, "is this the last member?") and by
        the despublicación cascade in `confirmar_relacion`/`revocar_relacion`
        (tasks 3.12, 3.15-3.16; design.md decisión 4, step 1: "Consulta qué
        agentes pertenecen a la agencia revocada")."""
        ...
