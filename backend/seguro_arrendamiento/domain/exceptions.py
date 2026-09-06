"""Domain-specific exceptions for the `seguro-arrendamiento` bounded context.

These extend `shared.domain.exceptions.DomainError`, following the same
base-exception pattern already used across the project (see
`shared/domain/exceptions.py`, `identidad/domain/exceptions.py`). Names omit
the "Error" suffix per `pyproject.toml`'s repo-wide convention for
`*/domain/exceptions.py` (`IdentidadYaVerificada`, `InmuebleNoEncontrado`,
etc.) — `docs/architecture/architecture.md` documents an older, unbuilt
`arrendamiento/` package with similarly-named exceptions
(`IdentidadNoVerificada`), reused here since this isolated
`seguro-arrendamiento` domain (per `proposal.md`) implements that same gate.
"""

from shared.domain.exceptions import DomainError


class IdentidadNoVerificada(DomainError):
    """Raised when an inquilino without `usuario.identidad_verificada = True`
    attempts to start a contratación de seguro de arrendamiento (spec.md:
    "Contratación de seguro de arrendamiento requiere identidad verificada").
    No `PolizaArrendamiento` is created and the proveedor externo de seguro
    is never called.
    """


class ContratacionNoDisponible(DomainError):
    """Raised by a `ProveedorSeguroArrendamientoPort` adapter (e.g.
    `SuraAdapter`) when the external provider cannot be reached (timeout,
    network error, unexpected response) — mapped by the API layer to an
    explicit "contratación no disponible, reintentar" response instead of a
    500, same rationale as `identidad.domain.exceptions.ValidacionNoDisponible`.
    """


class PolizaRechazadaNoPuedeActivarse(DomainError):
    """Raised when `PolizaArrendamiento.activar` is called on a póliza in
    estado `rechazada` — invariant documented in design.md's "Estrategia de
    testing": "invariante de que una póliza rechazada no puede activarse".
    """
