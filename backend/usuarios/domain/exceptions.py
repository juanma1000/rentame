"""Domain-specific exceptions for the `usuarios` bounded context.

These extend `shared.domain.exceptions.DomainError`, following the same
base-exception pattern used across the project (see
`shared/domain/exceptions.py` and `agencias/domain/exceptions.py`). They are
raised by use cases and translated to HTTP responses by the API layer.
"""

from shared.domain.exceptions import DomainError


class EmailYaRegistrado(DomainError):
    """Raised when attempting to register a new `Usuario` with an email that
    already has an account associated (spec.md: "Registro rechazado por
    email ya existente")."""


class CredencialesInvalidas(DomainError):
    """Raised on login when the email does not exist OR the password does
    not match — deliberately the SAME exception for both cases, so the
    caller cannot infer which email is registered (design.md decisión 5,
    spec.md: "Login rechazado sin revelar cuál dato falló")."""
