"""Base domain exceptions shared across all bounded contexts."""


class DomainError(Exception):
    """Base class for all domain-level exceptions.

    Domain exceptions represent violations of business rules. They are raised
    by entities, value objects and use cases, and translated to HTTP responses
    by the API layer (never the other way around).
    """


class DomainValidationError(DomainError):
    """Raised when an entity or value object is constructed with invalid data."""
