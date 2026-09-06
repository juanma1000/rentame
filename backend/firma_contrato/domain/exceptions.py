"""Domain-specific exceptions for the `firma-contrato` bounded context.

Extend `shared.domain.exceptions.DomainError`, following the same
base-exception pattern already used across the project (see
`shared/domain/exceptions.py`, `seguro_arrendamiento/domain/exceptions.py`).
Names omit the "Error" suffix per `pyproject.toml`'s repo-wide convention
for `*/domain/exceptions.py`.

`docs/architecture/architecture.md` documents an older, unbuilt
`arrendamiento/` package (a different, wider design covering
`SOLICITUD_ARRENDAMIENTO` end-to-end) with exceptions named
`SolicitudNoValida`, `IdentidadNoVerificada`, `ContratoNoFirmado` — none of
those map 1:1 onto this narrower `firma-contrato` domain (task 1.6): this
change's gate is "póliza aprobada", not "identidad verificada"
(`seguro_arrendamiento` already owns that gate), and there is no
`SolicitudArrendamiento` aggregate here. New, domain-specific names are used
instead, keeping the same "no Error suffix" convention.
"""

from shared.domain.exceptions import DomainError


class PolizaNoAprobada(DomainError):
    """Raised when an inquilino without a `PolizaArrendamiento` in estado
    `aprobada` attempts to start generating a contrato de arrendamiento
    (spec.md: "Generación de contrato requiere póliza aprobada"). No
    `Contrato` is created and the proveedor de firma electrónica is never
    called.
    """


class ContratoYaFirmado(DomainError):
    """Raised when a state-transition method (`enviar_a_firma`,
    `marcar_firmado`, `marcar_rechazado`, `marcar_expirado`) is called on a
    `Contrato` already in estado `firmado` — the invariant fixed by
    spec.md's "Un contrato firmado no puede reenviarse a firma": a signed
    contrato can never regress to an earlier estado.
    """


class ContratoNoEncontrado(DomainError):
    """Raised when the webhook reports a resultado de firma for a
    `referencia_externa` that does not match any known `Contrato`."""


class ContratoNoEnviadoAFirma(DomainError):
    """Raised when the webhook reports a resultado de firma
    (`firmado`/`rechazado`/`expirado`) for a `Contrato` that is not
    currently in estado `enviado_a_firma` (e.g. still `borrador`, or
    already resolved) — a duplicate/out-of-order webhook delivery, per
    design.md's "Firma asíncrona vía webhook introduce estado intermedio".
    """


class ArrendamientoRequiereContratoFirmado(DomainError):
    """Raised when `ArrendamientoActivo.crear` is called with a `Contrato`
    not in estado `firmado` — spec.md's "Contrato firmado crea un
    arrendamiento activo" ("ÚNICAMENTE cuando un Contrato pasa a estado
    firmado").
    """


class EnvioFirmaNoDisponible(DomainError):
    """Raised by a `ProveedorFirmaElectronicaPort` adapter (e.g.
    `ViafirmaAdapter`) when the external provider cannot be reached
    (timeout, network error, unexpected response) — mapped by the API
    layer to an explicit "envío a firma no disponible" response instead of
    a 500, same rationale as
    `seguro_arrendamiento.domain.exceptions.ContratacionNoDisponible`.
    """
