"""`Contrato` aggregate.

Business rules come from
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`
(Requirement: "Resultado modelado como contrato con estado propio") and
task 1.1-1.2 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`.

Per design.md decisión 2, this aggregate only tracks the firma process
itself (borrador -> enviado_a_firma -> firmado/rechazado/expirado) — the
legal content of the contrato is produced by
`firma_contrato.application.generar_contrato`'s own template (task 3.3) and
referenced here only as `documento_referencia` (opaque to this aggregate).

`inmueble_id` is carried on this aggregate (not only on
`ArrendamientoActivo`) because it is the only aggregate alive during the
async gap between "enviado a firma" and the webhook's resultado (design.md:
"estado intermedio ... sin garantía de cuándo llega el resultado") — it
must survive that gap so `procesar_resultado_firma` can build
`ArrendamientoActivo.inmueble_id` once the firma is reported `firmado`.
`PolizaArrendamiento` has no `inmueble_id` field to read it back from
(task 3.2's command supplies it directly), so this is the only place it can
live between the two use cases.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from firma_contrato.domain.exceptions import ContratoYaFirmado


class EstadoContrato(str, Enum):
    BORRADOR = "borrador"
    ENVIADO_A_FIRMA = "enviado_a_firma"
    FIRMADO = "firmado"
    RECHAZADO = "rechazado"
    EXPIRADO = "expirado"


# States a `Contrato` can never leave once reached — spec.md's "Un contrato
# firmado no puede reenviarse a firma" is the named scenario, but the same
# invariant applies to `rechazado`/`expirado`: none of them can transition
# anywhere else either.
_ESTADOS_FINALES = frozenset(
    {EstadoContrato.FIRMADO, EstadoContrato.RECHAZADO, EstadoContrato.EXPIRADO}
)


@dataclass
class Contrato:
    """A single contrato de arrendamiento generation and its subsequent
    firma lifecycle.

    Instances must be built through `Contrato.generar`. `id` is `None`
    until a repository assigns one on insert — same pattern as
    `PolizaArrendamiento`/`ValidacionIdentidad`.
    """

    usuario_id: uuid.UUID
    poliza_id: uuid.UUID
    inmueble_id: uuid.UUID
    estado: EstadoContrato
    documento_referencia: str
    fecha: datetime
    referencia_externa: str | None = None
    id: uuid.UUID | None = None

    @classmethod
    def generar(
        cls,
        *,
        usuario_id: uuid.UUID,
        poliza_id: uuid.UUID,
        inmueble_id: uuid.UUID,
        documento_referencia: str,
    ) -> Contrato:
        """Start a new `Contrato` in estado `borrador`, already carrying the
        generated legal document's reference (spec.md: "El contenido legal
        del contrato lo genera Rentame")."""
        return cls(
            usuario_id=usuario_id,
            poliza_id=poliza_id,
            inmueble_id=inmueble_id,
            estado=EstadoContrato.BORRADOR,
            documento_referencia=documento_referencia,
            fecha=datetime.now(UTC),
        )

    def _asegurar_no_finalizado(self) -> None:
        if self.estado in _ESTADOS_FINALES:
            raise ContratoYaFirmado(
                f"El contrato {self.id} ya está en estado final ({self.estado.value}) "
                "y no puede cambiar de estado"
            )

    def enviar_a_firma(self, *, referencia_externa: str) -> None:
        """Transition this contrato to estado `enviado_a_firma`, per
        spec.md's "Contrato pasa de borrador a enviado a firma"."""
        self._asegurar_no_finalizado()
        self.estado = EstadoContrato.ENVIADO_A_FIRMA
        self.referencia_externa = referencia_externa
        self.fecha = datetime.now(UTC)

    def marcar_firmado(self) -> None:
        """Transition an `enviado_a_firma` contrato to `firmado`.

        Raises `ContratoYaFirmado` when called on a contrato already in a
        final estado (`firmado`/`rechazado`/`expirado`) — the invariant
        fixed by spec.md's "Un contrato firmado no puede reenviarse a
        firma".
        """
        self._asegurar_no_finalizado()
        self.estado = EstadoContrato.FIRMADO
        self.fecha = datetime.now(UTC)

    def marcar_rechazado(self) -> None:
        """Transition an `enviado_a_firma` contrato to `rechazado`."""
        self._asegurar_no_finalizado()
        self.estado = EstadoContrato.RECHAZADO
        self.fecha = datetime.now(UTC)

    def marcar_expirado(self) -> None:
        """Transition an `enviado_a_firma` contrato to `expirado`."""
        self._asegurar_no_finalizado()
        self.estado = EstadoContrato.EXPIRADO
        self.fecha = datetime.now(UTC)
