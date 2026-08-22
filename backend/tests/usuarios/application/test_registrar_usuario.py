"""Unit tests for the `registrar_usuario` use case
(`usuarios/application/registrar_usuario.py`).

Covers the "Registro como propietario o inquilino" and "Registro como agente
requiere resolver el paso de agencia" requirements of
`openspec/changes/hu-008/specs/usuarios/spec.md` — specifically the parts
that concern account creation itself (the agencia step, per design.md
decisión 1, is NOT orchestrated here; `usuarios/application` never imports
anything from `agencias`).

TDD Red phase: `usuarios/application/registrar_usuario.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it. This file fixes, by construction, the
contract `backend-expert` must satisfy:

- `RegistrarUsuarioCommand`: a plain dataclass with `email: str`,
  `password: str`, `nombre: str`, `rol: str`.
- `registrar_usuario(command, *, usuario_repository) -> Usuario`: an async
  function that:
  1. Raises `usuarios.domain.exceptions.EmailYaRegistrado` when
     `usuario_repository.obtener_por_email(command.email)` already returns a
     `Usuario` — without calling `usuario_repository.guardar`.
  2. Otherwise builds `Usuario.crear(email=..., password=..., nombre=...,
     rol=...)` and persists it via `usuario_repository.guardar`.
"""

import pytest

from usuarios.application.registrar_usuario import (
    RegistrarUsuarioCommand,
    registrar_usuario,
)
from usuarios.domain.exceptions import EmailYaRegistrado
from usuarios.domain.usuario import Usuario
from tests.usuarios.application.conftest import FakeUsuarioRepository


def _valid_command(**overrides: object) -> RegistrarUsuarioCommand:
    kwargs: dict[str, object] = {
        "email": "nueva.persona@example.com",
        "password": "una-contrasena-segura",
        "nombre": "Nueva Persona",
        "rol": "propietario",
    }
    kwargs.update(overrides)
    return RegistrarUsuarioCommand(**kwargs)


class TestRegistrarUsuario:
    @pytest.mark.parametrize("rol", ["propietario", "agente", "inquilino"])
    async def test_should_create_and_persist_usuario_with_the_chosen_rol(
        self,
        rol: str,
        fake_usuario_repository: FakeUsuarioRepository,
    ) -> None:
        # Arrange
        command = _valid_command(rol=rol)

        # Act
        usuario = await registrar_usuario(
            command,
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert usuario.id is not None
        assert usuario.rol == rol
        assert usuario.email == command.email
        assert fake_usuario_repository.guardar_calls == [usuario]


class TestRegistrarUsuarioRejectsEmailDuplicado:
    async def test_should_raise_email_ya_registrado_and_not_call_guardar(
        self,
        fake_usuario_repository: FakeUsuarioRepository,
    ) -> None:
        # Arrange
        email_existente = "ya.registrada@example.com"
        fake_usuario_repository.seed(
            Usuario.crear(
                email=email_existente,
                password="otra-clave",
                nombre="Persona Existente",
                rol="inquilino",
            )
        )
        command = _valid_command(email=email_existente)

        # Act / Assert
        with pytest.raises(EmailYaRegistrado):
            await registrar_usuario(
                command,
                usuario_repository=fake_usuario_repository,
            )

        assert fake_usuario_repository.guardar_calls == []
