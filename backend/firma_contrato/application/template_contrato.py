"""Template propio del contrato de arrendamiento.

Task 3.3 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`, per
spec.md's "El contenido legal del contrato lo genera Rentame": the
proveedor de firma electrónica (`ProveedorFirmaElectronicaPort`) never
generates legal content — it only receives the text produced here.

`_DURACION_MINIMA_MESES` enforces the PRD's "duración mínima 6 meses" —
raising here (not silently clamping) so a caller who passes a shorter
duración gets an explicit, loud failure instead of an unnoticed contract
term.
"""

from __future__ import annotations

_DURACION_MINIMA_MESES = 6


class DuracionContratoInvalida(ValueError):
    """Raised when `generar_documento_contrato` is asked to produce a
    contrato with `duracion_meses` below the PRD's minimum of 6 months."""


def generar_documento_contrato(
    *,
    nombre_inquilino: str,
    nombre_propietario: str,
    direccion_inmueble: str,
    canon_mensual: float,
    duracion_meses: int,
) -> str:
    """Return the full legal text of a contrato de arrendamiento, built
    from Rentame's own template — partes, canon, duración — per the PRD's
    duración mínima de 6 meses.

    Raises `DuracionContratoInvalida` when `duracion_meses` is below 6.
    """
    if duracion_meses < _DURACION_MINIMA_MESES:
        raise DuracionContratoInvalida(
            f"La duración del contrato ({duracion_meses} meses) es menor a la "
            f"mínima permitida ({_DURACION_MINIMA_MESES} meses)"
        )

    return (
        "CONTRATO DE ARRENDAMIENTO DE VIVIENDA URBANA\n\n"
        f"Entre {nombre_propietario}, en calidad de ARRENDADOR, y "
        f"{nombre_inquilino}, en calidad de ARRENDATARIO, se celebra el "
        "presente contrato de arrendamiento, regido por la Ley 820 de 2003 "
        "y demás normas concordantes, bajo las siguientes cláusulas:\n\n"
        f"PRIMERA. OBJETO: El ARRENDADOR entrega al ARRENDATARIO, a título "
        f"de arrendamiento, el inmueble ubicado en {direccion_inmueble}.\n\n"
        f"SEGUNDA. CANON: El canon de arrendamiento mensual es de "
        f"${canon_mensual:,.2f}, pagadero por mensualidades anticipadas.\n\n"
        f"TERCERA. DURACIÓN: El presente contrato tendrá una duración de "
        f"{duracion_meses} meses, contados a partir de la fecha de firma "
        "por ambas partes.\n\n"
        "CUARTA. FIRMA ELECTRÓNICA: Las partes aceptan suscribir el "
        "presente contrato mediante firma electrónica, con plena validez "
        "legal conforme a la Ley 527 de 1999."
    )
