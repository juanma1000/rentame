"""Unit tests for the `Agencia` entity (`agencias/domain/agencia.py`).

Pure domain tests: no database, no HTTP. They express the "Creación de
agencia" requirement from
`openspec/changes/hu-007/specs/agencias/spec.md` (task 1.1 of
`openspec/changes/hu-007/tasks.md`).

TDD Red phase: `agencias/domain/agencia.py` does not exist yet, so this test
is expected to fail with `ModuleNotFoundError` until `backend-expert`
implements it (task 2.1). This file defines, by construction, the contract
the implementation must satisfy:

- `Agencia.crear(*, razon_social, nit)` is a factory classmethod that
  validates all business invariants up front and returns an `Agencia` with
  `id is None` (the identifier is assigned by the repository on insert, same
  pattern as `Inmueble.crear` in `inmuebles/domain/inmueble.py`).
- `razon_social` and `nit` must be non-empty strings; a blank value raises
  `shared.domain.exceptions.DomainValidationError`.
"""

import pytest

from agencias.domain.agencia import Agencia
from shared.domain.exceptions import DomainValidationError


def _valid_agencia_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "razon_social": "Inmobiliaria del Valle S.A.S.",
        "nit": "900123456-7",
    }
    kwargs.update(overrides)
    return kwargs


class TestAgenciaCrear:
    def test_should_create_agencia_with_razon_social_and_nit_when_data_is_valid(self) -> None:
        # Arrange
        kwargs = _valid_agencia_kwargs()

        # Act
        agencia = Agencia.crear(**kwargs)

        # Assert
        assert agencia.razon_social == kwargs["razon_social"]
        assert agencia.nit == kwargs["nit"]
        assert agencia.id is None

    def test_should_raise_domain_validation_error_when_razon_social_is_blank(self) -> None:
        # Arrange
        kwargs = _valid_agencia_kwargs(razon_social="   ")

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Agencia.crear(**kwargs)

    def test_should_raise_domain_validation_error_when_nit_is_blank(self) -> None:
        # Arrange
        kwargs = _valid_agencia_kwargs(nit="")

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Agencia.crear(**kwargs)
