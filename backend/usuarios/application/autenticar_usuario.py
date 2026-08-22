"""`autenticar_usuario` use case.

Orchestrates the "Inicio de sesión con email y contraseña" requirement of
`openspec/changes/hu-008/specs/usuarios/spec.md`, and `design.md` decisión 5:
login rejects with a single, undifferentiated exception regardless of
whether the email is unknown or the password is wrong — the caller can never
tell which one it was.
"""

from __future__ import annotations

from dataclasses import dataclass

from usuarios.domain.exceptions import CredencialesInvalidas
from usuarios.domain.ports import UsuarioRepositoryPort
from usuarios.domain.usuario import Usuario


@dataclass
class AutenticarUsuarioCommand:
    email: str
    password: str


async def autenticar_usuario(
    command: AutenticarUsuarioCommand,
    *,
    usuario_repository: UsuarioRepositoryPort,
) -> Usuario:
    """Return the `Usuario` matching `command.email`/`command.password`.

    Raises `CredencialesInvalidas` both when the email does not exist and
    when the password does not match its hash — always the same exception,
    so a caller cannot infer which email is registered.
    """
    usuario = await usuario_repository.obtener_por_email(command.email)
    if usuario is None or not usuario.verificar_password(command.password):
        raise CredencialesInvalidas("Email o contraseña incorrectos")

    return usuario
