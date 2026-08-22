"""`Agencia` entity.

Business rules come from `openspec/changes/hu-007/specs/agencias/spec.md`
(Requirement: "Creación de agencia", task 1.1 of
`openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from shared.domain.exceptions import DomainValidationError


@dataclass
class Agencia:
    """A real-estate agency, owned/represented by an agente.

    Instances must be built through `Agencia.crear`, which enforces every
    creation-time invariant.

    `id` is `None` until a repository assigns one on insert — same pattern as
    `Inmueble.crear` in `inmuebles/domain/inmueble.py`.
    """

    razon_social: str
    nit: str
    id: uuid.UUID | None = None

    @classmethod
    def crear(cls, *, razon_social: str, nit: str) -> Agencia:
        """Validate business invariants and create a new `Agencia`.

        Raises `DomainValidationError` when `razon_social` or `nit` is blank.
        """
        if not razon_social.strip():
            raise DomainValidationError("razon_social cannot be blank")
        if not nit.strip():
            raise DomainValidationError("nit cannot be blank")

        return cls(razon_social=razon_social, nit=nit)
