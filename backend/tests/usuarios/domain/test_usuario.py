"""Unit tests for the `Usuario` entity (`usuarios/domain/usuario.py`).

Pure domain tests: no database, no HTTP. They express the "Registro como
propietario o inquilino" and "Rol único y fijo por cuenta" requirements from
`openspec/changes/hu-008/specs/usuarios/spec.md`, plus design.md decisión 2
(bcrypt hashing, `password_hash` never exposed in plain form).

TDD Red phase: `usuarios/domain/usuario.py` does not exist yet, so every test
here is expected to fail with `ModuleNotFoundError` until `backend-expert`
implements it. This file fixes, by construction, the contract the
implementation must satisfy:

- `Usuario.crear(*, email, password, nombre, rol)` is a factory classmethod
  that hashes `password` with bcrypt into `password_hash` and returns a
  `Usuario` with `id is None` (assigned by the repository on insert, same
  pattern as `Agencia.crear`/`Inmueble.crear`).
- `Usuario` never stores the plaintext password: there is no `password`
  attribute, only `password_hash`.
- `usuario.verificar_password(password)` returns `True` for the correct
  plaintext password and `False` otherwise.
- `rol` is fixed to whatever value was passed to `crear` (`propietario`,
  `agente`, or `inquilino`).
"""

import pytest

from usuarios.domain.usuario import Usuario


def _valid_usuario_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "email": "persona@example.com",
        "password": "una-contrasena-segura",
        "nombre": "Persona Ejemplo",
        "rol": "propietario",
    }
    kwargs.update(overrides)
    return kwargs


class TestUsuarioCrear:
    def test_should_hash_password_so_it_never_matches_plaintext(self) -> None:
        # Arrange
        kwargs = _valid_usuario_kwargs(password="clave-plana-123")

        # Act
        usuario = Usuario.crear(**kwargs)

        # Assert
        assert usuario.password_hash != "clave-plana-123"

    def test_should_produce_a_different_hash_on_each_call_due_to_salt(self) -> None:
        # Arrange
        kwargs = _valid_usuario_kwargs()

        # Act
        usuario_uno = Usuario.crear(**kwargs)
        usuario_dos = Usuario.crear(**kwargs)

        # Assert
        assert usuario_uno.password_hash != usuario_dos.password_hash

    def test_should_not_expose_a_plaintext_password_attribute(self) -> None:
        # Arrange
        kwargs = _valid_usuario_kwargs()

        # Act
        usuario = Usuario.crear(**kwargs)

        # Assert
        assert not hasattr(usuario, "password")

    def test_should_set_id_to_none_until_a_repository_assigns_one(self) -> None:
        # Arrange
        kwargs = _valid_usuario_kwargs()

        # Act
        usuario = Usuario.crear(**kwargs)

        # Assert
        assert usuario.id is None

    @pytest.mark.parametrize("rol", ["propietario", "agente", "inquilino"])
    def test_should_fix_rol_to_the_value_passed_at_creation(self, rol: str) -> None:
        # Arrange
        kwargs = _valid_usuario_kwargs(rol=rol)

        # Act
        usuario = Usuario.crear(**kwargs)

        # Assert
        assert usuario.rol == rol


class TestUsuarioVerificarPassword:
    def test_should_return_true_when_password_is_correct(self) -> None:
        # Arrange
        usuario = Usuario.crear(**_valid_usuario_kwargs(password="clave-correcta"))

        # Act
        resultado = usuario.verificar_password("clave-correcta")

        # Assert
        assert resultado is True

    def test_should_return_false_when_password_is_incorrect(self) -> None:
        # Arrange
        usuario = Usuario.crear(**_valid_usuario_kwargs(password="clave-correcta"))

        # Act
        resultado = usuario.verificar_password("clave-incorrecta")

        # Assert
        assert resultado is False
