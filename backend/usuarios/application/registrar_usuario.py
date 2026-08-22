"""`registrar_usuario` use case.

Orchestrates the "Registro como propietario o inquilino" and "Registro como
agente requiere resolver el paso de agencia" requirements of
`openspec/changes/hu-008/specs/usuarios/spec.md`, restricted to the account
creation itself — the agencia step (design.md decisión 1) is a frontend flow
that chains already-existing `agencias` endpoints, so this module never
imports anything from `agencias`.

This module only orchestrates: every creation-time invariant of `Usuario`
stays in `Usuario.crear` (never re-implemented here).
"""

from __future__ import annotations

from dataclasses import dataclass

from usuarios.domain.exceptions import EmailYaRegistrado
from usuarios.domain.ports import UsuarioRepositoryPort
from usuarios.domain.usuario import Usuario


@dataclass
class RegistrarUsuarioCommand:
    email: str
    password: str
    nombre: str
    rol: str


async def registrar_usuario(
    command: RegistrarUsuarioCommand,
    *,
    usuario_repository: UsuarioRepositoryPort,
) -> Usuario:
    """Create and persist a new `Usuario` account.

    Raises `EmailYaRegistrado` when `command.email` already has an account
    associated — in that case no `Usuario` is persisted.
    """
    if await usuario_repository.obtener_por_email(command.email) is not None:
        raise EmailYaRegistrado(f"El email {command.email} ya está registrado")

    usuario = Usuario.crear(
        email=command.email,
        password=command.password,
        nombre=command.nombre,
        rol=command.rol,
    )
    return await usuario_repository.guardar(usuario)
