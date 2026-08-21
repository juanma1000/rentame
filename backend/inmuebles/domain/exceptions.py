"""Domain-specific exceptions for the `inmuebles` bounded context.

These extend `shared.domain.exceptions.DomainError`, following the same
base-exception pattern already used across the project (see
`shared/domain/exceptions.py`). They are raised by use cases (a later phase,
tasks 3.x-4.x of `openspec/changes/hu-001/tasks.md`) and translated to HTTP
responses by the API layer.
"""

from shared.domain.exceptions import DomainError


class InmuebleNoEncontrado(DomainError):
    """Raised when an operation references an `Inmueble` id that does not exist."""


class PropietarioInvalido(DomainError):
    """Raised when the `propietario_id` performing a write does not match the
    `Inmueble`'s owner (spec.md: "Edición de inmueble publicado" —
    autorización por pertenencia, design.md decisión 5).
    """


class LimiteFotosExcedido(DomainError):
    """Raised when an operation would leave an `Inmueble` with a photo count
    outside `[1, MAX_FOTOS_INMUEBLE]` (e.g. adding/removing fotos on edit).
    """
