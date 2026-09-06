"""Domain-specific exceptions for the `identidad` bounded context.

These extend `shared.domain.exceptions.DomainError`, following the same
base-exception pattern already used across the project (see
`shared/domain/exceptions.py`, `agencias/domain/exceptions.py`). Names
match what `docs/architecture/architecture.md` already documents for this
package (`IdentidadYaVerificada`, `ValidacionNoDisponible`).
"""

from shared.domain.exceptions import DomainError


class IdentidadYaVerificada(DomainError):
    """Raised when a new validación is attempted for a cuenta that already
    has one `ValidacionIdentidad` in estado `aprobado` (spec.md: "Una sola
    validación exitosa por cuenta"). No new `ValidacionIdentidad` is created
    and the proveedor externo is never called.
    """


class ValidacionNoDisponible(DomainError):
    """Raised by a `ProveedorValidacionIdentidadPort` adapter (e.g.
    `TruoraAdapter`) when the external provider cannot be reached (timeout,
    network error, unexpected response) — mapped by the API layer to an
    explicit "validación no disponible, reintentar" response instead of a
    500, per design.md's risk mitigation for Truora's availability.
    """
