"""Domain-specific exceptions for the `agencias` bounded context.

These extend `shared.domain.exceptions.DomainError`, following the same
base-exception pattern already used across the project (see
`shared/domain/exceptions.py` and `inmuebles/domain/exceptions.py`). They are
raised by use cases (a later phase, tasks 3.x of
`openspec/changes/hu-007/tasks.md`) and translated to HTTP responses by the
API layer.
"""

from shared.domain.exceptions import DomainError


class AgenciaNoEncontrada(DomainError):
    """Raised when an operation references an `Agencia` id that does not exist."""


class SolicitudNoEncontrada(DomainError):
    """Raised when an operation references a `SolicitudIngreso` id that does not exist."""


class RelacionNoEncontrada(DomainError):
    """Raised when an operation references a `RelacionAgenciaPropietario` id that does
    not exist.
    """


class PropietarioInvalido(DomainError):
    """Raised when the `propietario_id` performing a write on a
    `RelacionAgenciaPropietario` does not match the relación's own
    `propietario_id` — e.g. revoking a relación that belongs to a different
    propietario. Same rationale/name as `inmuebles.domain.exceptions.
    PropietarioInvalido` (autorización por pertenencia).
    """


class AgenteYaTieneAgencia(DomainError):
    """Raised when an agente attempting to create or join an agencia already belongs
    to one (spec.md: "Máximo una agencia activa por propietario" analog for agentes).
    """


class RelacionYaActiva(DomainError):
    """Raised when a propietario attempts to start a new relación with an agencia
    while already having one `ACTIVA` (spec.md: "Máximo una agencia activa por
    propietario").
    """


class UltimoAgenteConRelacionesActivas(DomainError):
    """Raised when removing the last agente of an agencia would leave active
    `RelacionAgenciaPropietario` records without any responsable agente.
    """


class AgenteNoEsMiembroDeAgencia(DomainError):
    """Raised when an operation requires the acting (or target) agente to be a
    member of a specific `Agencia` and it is not — e.g. approving a
    `SolicitudIngreso` (spec.md: "Un miembro existente aprueba el ingreso"),
    confirming a `RelacionAgenciaPropietario` (spec.md: "Un agente de la
    agencia confirma la relación"), or reassigning `agente_responsable_id` to
    a non-member (spec.md: "Agente responsable reasignable"). Added in tasks
    3.x of `openspec/changes/hu-007/tasks.md` (use cases), since none of the
    entity-level tests of section 1 needed it.
    """
