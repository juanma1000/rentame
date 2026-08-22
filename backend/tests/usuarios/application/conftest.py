"""In-memory fake for the `usuarios` outbound port (`UsuarioRepositoryPort`,
still to be defined in `usuarios/domain/ports.py`).

Test double only — no production code lives here. Same pattern as
`tests/agencias/application/conftest.py` from HU-007: the fake satisfies the
port structurally (no inheritance needed), and tests seed it directly instead
of going through a use case.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from usuarios.domain.usuario import Usuario


@dataclass
class FakeUsuarioRepository:
    """In-memory stand-in for `UsuarioRepositoryPort`."""

    _usuarios_por_id: dict[UUID, Usuario] = field(default_factory=dict)
    _usuarios_por_email: dict[str, Usuario] = field(default_factory=dict)
    guardar_calls: list[Usuario] = field(default_factory=list)

    def seed(self, usuario: Usuario) -> Usuario:
        if usuario.id is None:
            usuario.id = uuid4()
        self._usuarios_por_id[usuario.id] = usuario
        self._usuarios_por_email[usuario.email] = usuario
        return usuario

    async def guardar(self, usuario: Usuario) -> Usuario:
        self.guardar_calls.append(usuario)
        usuario.id = uuid4()
        self._usuarios_por_id[usuario.id] = usuario
        self._usuarios_por_email[usuario.email] = usuario
        return usuario

    async def obtener_por_email(self, email: str) -> Usuario | None:
        return self._usuarios_por_email.get(email)

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        return self._usuarios_por_id.get(usuario_id)


@pytest.fixture
def fake_usuario_repository() -> FakeUsuarioRepository:
    return FakeUsuarioRepository()
