"""Domain-specific exceptions for the `pagos` bounded context.

Extend `shared.domain.exceptions.DomainError`, following the same
base-exception pattern already used across the project (see
`shared/domain/exceptions.py`, `firma_contrato/domain/exceptions.py`).
Names omit the "Error" suffix per `pyproject.toml`'s repo-wide convention
for `*/domain/exceptions.py`.

`docs/architecture/architecture.md` documents an older, unbuilt
`arrendamiento/` package's `PAGO` entity (estado
`pendiente|procesando|completado|fallido|reembolsado`, `metodo`,
`comprobante_storage_key`, etc.) — that is a wider design for an
end-to-end `SOLICITUD_ARRENDAMIENTO` flow this project never built (same
caveat already documented in `firma_contrato/domain/exceptions.py`), not
this narrower `pago-mensual-renta` change's contract. No exception names
are documented there for a `pagos` domain built on top of
`ArrendamientoActivo`, so new, domain-specific names are used here instead,
keeping the same "no Error suffix" convention.
"""

from shared.domain.exceptions import DomainError


class PagoYaCompletado(DomainError):
    """Raised when a state-transition method (`registrar_intento`,
    `marcar_completado`, `marcar_fallido`) is called on a `Pago` already
    `completado` — the invariant fixed by spec.md's "Un pago ya completado
    no puede reiniciarse": a completed pago can never regress to an
    earlier estado nor change its result again. Also raised by
    `pagos.application.iniciar_pago` when the caller attempts to
    (re)iniciar a `Pago` already in estado `completado`.
    """


class PagoNoEncontrado(DomainError):
    """Raised when `pagos.application.iniciar_pago` or
    `pagos.application.procesar_resultado_pago` look up a `Pago` (by `id`
    or by `referencia_externa`) that does not exist.
    """


class ArrendamientoActivoNoEncontrado(DomainError):
    """Raised by `pagos.application.iniciar_pago` when the
    `ArrendamientoActivo` a `Pago` refers to (or the data needed from it —
    póliza/inmueble) cannot be found via `ArrendamientoActivoPort` — a
    referential-integrity condition that should not happen in practice
    (every `Pago` is created off an existing `ArrendamientoActivo`), kept
    explicit instead of surfacing as an unhandled `AttributeError`.
    """


class CobroPagoNoDisponible(DomainError):
    """Raised by a `PasarelaPagosPort` adapter (e.g. `WompiAdapter`) when
    the external provider cannot be reached (timeout, network error,
    unexpected response) — mapped by the API layer to an explicit "cobro
    no disponible" response instead of a 500, same rationale as
    `firma_contrato.domain.exceptions.EnvioFirmaNoDisponible`.
    """
