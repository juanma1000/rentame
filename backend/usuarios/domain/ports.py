"""Outbound port for the `usuarios` domain.

This `Protocol` is the interface the application layer
(`usuarios/application/`) depends on instead of depending on concrete
infrastructure. A concrete adapter is implemented in
`usuarios/infrastructure/` in a later phase, per
`docs/architecture/architecture.md`'s hexagonal layout for this domain.

Methods are `async` because the project's persistence layer is built on
SQLAlchemy's async engine/session (see `shared/infrastructure/database.py`),
following the same pattern as `agencias/domain/ports.py`.

`Protocol` (structural typing) is used rather than `ABC`, same rationale as
`agencias/domain/ports.py`: adapters (and test fakes) only need to match the
shape, not inherit from a common base.
"""

from typing import Protocol
from uuid import UUID

from usuarios.domain.usuario import Usuario


class UsuarioRepositoryPort(Protocol):
    """Persistence contract for the `Usuario` aggregate."""

    async def guardar(self, usuario: Usuario) -> Usuario:
        """Insert a new `Usuario` and return it with `id` set."""
        ...

    async def obtener_por_email(self, email: str) -> Usuario | None:
        """Return the `Usuario` matching `email`, or `None` if it does not exist."""
        ...

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        """Return the `Usuario` matching `usuario_id`, or `None` if it does not exist."""
        ...
