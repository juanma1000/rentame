"""Unit tests for the `autenticar_usuario` use case
(`usuarios/application/autenticar_usuario.py`).

Covers the "Inicio de sesión con email y contraseña" requirement of
`openspec/changes/hu-008/specs/usuarios/spec.md`, and design.md decisión 5:
login rejects with a single, undifferentiated exception regardless of
whether the email is unknown or the password is wrong (never reveals which).

TDD Red phase: `usuarios/application/autenticar_usuario.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it. This file fixes, by construction, the
contract `backend-expert` must satisfy:

- `AutenticarUsuarioCommand`: a plain dataclass with `email: str`,
  `password: str`.
- `autenticar_usuario(command, *, usuario_repository) -> Usuario`: an async
  function that:
  1. Returns the matching `Usuario` when the email exists and the password
     matches its hash (`usuario.verificar_password(...)` is `True`).
  2. Raises `usuarios.domain.exceptions.CredencialesInvalidas` when the email
     does not exist at all.
  3. Raises the SAME `CredencialesInvalidas` exception when the email exists
     but the password does not match — never a different/more specific
     exception, so the two failure modes are indistinguishable from the
     caller's perspective.
"""

import pytest

from usuarios.application.autenticar_usuario import (
    AutenticarUsuarioCommand,
    autenticar_usuario,
)
from usuarios.domain.exceptions import CredencialesInvalidas
from usuarios.domain.usuario import Usuario
from tests.usuarios.application.conftest import FakeUsuarioRepository


class TestAutenticarUsuarioExitoso:
    async def test_should_return_usuario_when_email_exists_and_password_matches(
        self,
        fake_usuario_repository: FakeUsuarioRepository,
    ) -> None:
        # Arrange
        email = "cuenta.valida@example.com"
        password = "clave-correcta"
        usuario_registrado = fake_usuario_repository.seed(
            Usuario.crear(
                email=email,
                password=password,
                nombre="Cuenta Valida",
                rol="propietario",
            )
        )

        # Act
        usuario = await autenticar_usuario(
            AutenticarUsuarioCommand(email=email, password=password),
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert usuario.id == usuario_registrado.id
        assert usuario.email == email


class TestAutenticarUsuarioRejectsEmailInexistente:
    async def test_should_raise_credenciales_invalidas_when_email_does_not_exist(
        self,
        fake_usuario_repository: FakeUsuarioRepository,
    ) -> None:
        # Arrange / Act / Assert
        with pytest.raises(CredencialesInvalidas):
            await autenticar_usuario(
                AutenticarUsuarioCommand(
                    email="no.existe@example.com",
                    password="cualquier-clave",
                ),
                usuario_repository=fake_usuario_repository,
            )


class TestAutenticarUsuarioRejectsPasswordIncorrecto:
    async def test_should_raise_the_same_credenciales_invalidas_when_password_is_wrong(
        self,
        fake_usuario_repository: FakeUsuarioRepository,
    ) -> None:
        # Arrange
        email = "cuenta.valida@example.com"
        fake_usuario_repository.seed(
            Usuario.crear(
                email=email,
                password="clave-correcta",
                nombre="Cuenta Valida",
                rol="inquilino",
            )
        )

        # Act / Assert
        with pytest.raises(CredencialesInvalidas):
            await autenticar_usuario(
                AutenticarUsuarioCommand(email=email, password="clave-incorrecta"),
                usuario_repository=fake_usuario_repository,
            )
