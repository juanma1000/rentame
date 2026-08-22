"""`buscar_agencias` use case.

Covers the "Búsqueda pública de agencias" requirement of
`openspec/changes/hu-008/specs/agencias/spec.md`. Per `design.md` decisión
4, this is a read-only pass-through to `AgenciaRepositoryPort.buscar` — kept
as its own use case only for consistency with the rest of the project (every
other read/write in `agencias/application` goes through one).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agencias.domain.agencia import Agencia


class _AgenciaBuscarPort(Protocol):
    """Minimal port this use case depends on.

    Kept local (not added to `agencias.domain.ports.AgenciaRepositoryPort`)
    because `buscar` on the real port/adapter is a separate, later task
    (task 5.4 of `openspec/changes/hu-008/tasks.md`) — extending the shared
    port here, ahead of its Postgres implementation, would break every
    other caller that depends on `AgenciaRepositoryPort` being fully
    implemented by `AgenciaRepositoryPostgres`.
    """

    async def buscar(self, texto: str) -> list[Agencia]:
        """Return every `Agencia` whose `razon_social`/`nit` matches `texto`
        (case-insensitive substring), empty list if none."""
        ...


@dataclass
class BuscarAgenciasCommand:
    texto: str


async def buscar_agencias(
    command: BuscarAgenciasCommand,
    *,
    agencia_repository: _AgenciaBuscarPort,
) -> list[Agencia]:
    """Return every `Agencia` whose razón social or NIT matches `command.texto`.

    Delegates entirely to `agencia_repository.buscar` — an empty list is a
    normal result (no matches), never an exception.
    """
    return await agencia_repository.buscar(command.texto)
