"""Pydantic schemas for the `usuarios` HTTP API (tasks 4.2/4.4 of
`openspec/changes/hu-008/tasks.md`).

Follows the `AgenciaResponse`/`AgenciaCreateRequest` precedent
(`agencias/infrastructure/api/schemas.py`): every `*Response` is built from
the corresponding domain entity via a `from_domain` classmethod, and never
exposes `password`/`password_hash` — `UsuarioResponse` simply has no field
for it.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from usuarios.domain.usuario import Usuario


class RegistroRequest(BaseModel):
    """JSON body accepted by `POST /usuarios/registro`."""

    email: str
    password: str
    nombre: str
    rol: str


class LoginRequest(BaseModel):
    """JSON body accepted by `POST /usuarios/login`."""

    email: str
    password: str


class UsuarioResponse(BaseModel):
    """Public representation of a `Usuario` — never includes `password`/
    `password_hash`."""

    id: uuid.UUID
    email: str
    nombre: str
    rol: str

    @classmethod
    def from_domain(cls, usuario: Usuario) -> UsuarioResponse:
        if usuario.id is None:
            raise ValueError("cannot build UsuarioResponse from a Usuario without an id")
        return cls(
            id=usuario.id,
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol,
        )


class AuthResponse(BaseModel):
    """Response body shared by `POST /usuarios/registro` and
    `POST /usuarios/login`."""

    access_token: str
    usuario: UsuarioResponse
