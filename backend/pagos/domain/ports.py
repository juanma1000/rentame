"""Outbound ports for the `pagos` domain.

`Protocol`s (structural typing), same rationale as
`firma_contrato/domain/ports.py` and `seguro_arrendamiento/domain/ports.py`
— adapters only need to match the shape, not inherit from a common base.
Methods are `async` for the same reason: the project's persistence layer
and any HTTP-backed adapter are built on async I/O.

`ArrendamientoActivoPort`/`PolizaArrendamientoPort`/`InmueblePort` are
read-only views this domain uses to reach data owned by
`firma_contrato`/`seguro_arrendamiento`/`inmuebles` without depending on
their infrastructure directly — same rationale as
`firma_contrato.domain.ports.PolizaArrendamientoPort` (design.md decisión
5: "cada aggregate consulta el aggregate inmediatamente anterior en la
cadena, no salta capas"). None of their methods can ever change the data
they read.

`InmueblePort.obtener` doubles `valor_mensual` alongside `propietario_id`:
`canon_mensual` (the full monthly rent) is not persisted anywhere past
`firma_contrato.domain.contrato.Contrato.documento_referencia` (an opaque,
already-rendered legal text — see that module's docstring) nor
`ArrendamientoActivo`, so `Inmueble.valor_mensual` is the only surviving,
authoritative source this domain can read for the monto of each ciclo's
`Pago` — consistent with design.md's "el monto que ve/paga el inquilino es
el canon completo del arriendo".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from pagos.domain.pago import Pago


@dataclass
class SplitPago:
    """Split parameters passed to a `PasarelaPagosPort` adapter's
    `iniciar_cobro`, assembled by `pagos.application.iniciar_pago` from
    `ArrendamientoActivo`/`PolizaArrendamiento`/`Inmueble`.

    Never persisted as its own aggregate — per design.md decisión 3, the
    split is executed by the pasarela as a transaction parameter, not by
    Rentame's own funds-handling logic. `monto_prima_retenida` is the
    amount retained (the seguro de arrendamiento's prima mensual, paid by
    the propietario per HU-005 but retained out of the inquilino's pago);
    the pasarela is expected to route the remainder
    (`monto_total - monto_prima_retenida`) to `propietario_id`.
    """

    monto_total: float
    monto_prima_retenida: float
    propietario_id: UUID


@dataclass
class ResultadoCobro:
    """Outcome of a single call to a `PasarelaPagosPort` adapter's
    `iniciar_cobro`.

    `estado` is the proveedor's own vocabulary for whether the cobro
    resolved synchronously (`"completado"` — `FakeAdapter`'s only
    possible value, per design.md's flow "Fake: completa inmediato") or is
    still in flight, to be resolved later via `POST /pagos/webhook`
    (anything else, e.g. `"pendiente"` — Wompi's async flow per design.md's
    sequence diagram: "Wompi: async, webhook luego"). Intentionally a
    plain `str` (not `EstadoPago`), mapped onto it inside
    `pagos.application.iniciar_pago`, not here.
    """

    referencia_externa: str
    estado: str


@dataclass
class ResultadoWebhookPago:
    """The payload a pasarela de pagos reports back (via webhook) once a
    cobro reaches a terminal outcome.

    `estado` is one of `"completado"`, `"fallido"` — intentionally a plain
    `str` (not `EstadoPago`), mapped onto it inside
    `pagos.application.procesar_resultado_pago`, not here.
    """

    referencia_externa: str
    estado: str


class PasarelaPagosPort(Protocol):
    """Contract every pasarela de pagos provider adapter must satisfy
    (`FakeAdapter` for dev/test, `WompiAdapter` for prod).

    Raises `pagos.domain.exceptions.CobroPagoNoDisponible` when the
    external provider cannot be reached (timeout/network/unexpected
    response) — never lets that failure surface as an unhandled
    exception, so the API layer can map it to an explicit "cobro no
    disponible" response instead of a 500.
    """

    async def iniciar_cobro(self, split: SplitPago) -> ResultadoCobro: ...


class PagoRepositoryPort(Protocol):
    """Persistence contract for the `Pago` aggregate."""

    async def guardar(self, pago: Pago) -> Pago:
        """Insert a new `Pago` and return it with `id` set."""
        ...

    async def actualizar(self, pago: Pago) -> Pago:
        """Persist a state change on an already-existing `Pago`."""
        ...

    async def obtener_por_id(self, pago_id: UUID) -> Pago | None:
        """Return the `Pago` with `pago_id`, or `None` if none exists."""
        ...

    async def obtener_por_referencia_externa(self, referencia_externa: str) -> Pago | None:
        """Return the `Pago` whose `referencia_externa` matches, used by
        the webhook to locate which pago a pasarela's payload refers to.
        `None` if no pago has that referencia."""
        ...

    async def listar_por_arrendamiento(self, arrendamiento_activo_id: UUID) -> list[Pago]:
        """Return every `Pago` (any estado) belonging to
        `arrendamiento_activo_id` — the full historial, per spec.md's
        "Historial de pagos por arrendamiento": "sin filtrar por
        estado"."""
        ...

    async def obtener_pendiente_por_arrendamiento(
        self, arrendamiento_activo_id: UUID
    ) -> Pago | None:
        """Return an unresolved (`pendiente`) `Pago` for
        `arrendamiento_activo_id`, or `None` if it has none — used by
        `pagos.application.generar_pagos_del_ciclo` to decide whether a
        new `Pago` needs to be created for the ciclo actual (spec.md: "El
        sistema NO SHALL generar un segundo Pago pendiente... mientras
        exista uno sin resolver")."""
        ...


@dataclass
class ArrendamientoActivoInfo:
    """The subset of `firma_contrato.domain.arrendamiento_activo.
    ArrendamientoActivo` this domain ever needs to read."""

    id: UUID
    poliza_id: UUID
    inmueble_id: UUID


class ArrendamientoActivoPort(Protocol):
    """Read-only view over `ArrendamientoActivo` (the `firma_contrato`
    domain), same rationale as
    `firma_contrato.domain.ports.PolizaArrendamientoPort` for reading
    `seguro_arrendamiento`'s data. This domain never modifies
    `ArrendamientoActivo`."""

    async def listar_activos(self) -> list[ArrendamientoActivoInfo]:
        """Return every currently-active `ArrendamientoActivo`, used by
        `pagos.application.generar_pagos_del_ciclo` to generate one
        `Pago` per ciclo for each."""
        ...

    async def obtener(self, arrendamiento_activo_id: UUID) -> ArrendamientoActivoInfo | None:
        """Return the `ArrendamientoActivo` with `arrendamiento_activo_id`,
        or `None` if none exists."""
        ...


class PolizaArrendamientoPort(Protocol):
    """Read-only view over `PolizaArrendamiento.prima_mensual`
    (`seguro_arrendamiento` domain) — this domain only ever reads the
    prima, never modifies it (proposal.md Impact: "lectura de
    PolizaArrendamiento.prima_mensual ... sin modificarlo")."""

    async def obtener_prima_mensual(self, poliza_id: UUID) -> float | None:
        """Return the `prima_mensual` of the `PolizaArrendamiento` with
        `poliza_id`, or `None` if the póliza does not exist or has no
        prima recorded."""
        ...


@dataclass
class InmuebleInfo:
    """The subset of `inmuebles.domain.inmueble.Inmueble` this domain
    ever needs to read."""

    propietario_id: UUID
    valor_mensual: float


class InmueblePort(Protocol):
    """Read-only view over `Inmueble.propietario_id`/`valor_mensual`
    (`inmuebles` domain) — this domain only ever reads these two fields,
    never modifies the inmueble (proposal.md Impact: "lectura de ...
    Inmueble.propietario_id ... sin modificarlo")."""

    async def obtener(self, inmueble_id: UUID) -> InmuebleInfo | None:
        """Return the `InmuebleInfo` for `inmueble_id`, or `None` if it
        does not exist."""
        ...
