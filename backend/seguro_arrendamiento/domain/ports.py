"""Outbound ports for the `seguro-arrendamiento` domain.

`Protocol`s (structural typing), same rationale as
`identidad/domain/ports.py` and `agencias/domain/ports.py` — adapters only
need to match the shape, not inherit from a common base. Methods are
`async` for the same reason: the project's persistence layer and any
HTTP-backed adapter are built on async I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from seguro_arrendamiento.domain.poliza_arrendamiento import PolizaArrendamiento


@dataclass
class ResultadoPoliza:
    """Outcome of a single call to a `ProveedorSeguroArrendamientoPort`
    adapter.

    `aprobada` is `True`/`False` for a definitive answer from the
    proveedor; `referencia_externa` is the proveedor's own tracking id
    (kept for audit/dispute purposes, same rationale as
    `identidad.domain.ports.ResultadoValidacion`). `prima_mensual`,
    `vigencia_desde` and `vigencia_hasta` are only populated when
    `aprobada` is `True`.
    """

    aprobada: bool
    referencia_externa: str
    prima_mensual: float | None = None
    vigencia_desde: date | None = None
    vigencia_hasta: date | None = None


class ProveedorSeguroArrendamientoPort(Protocol):
    """Contract every seguro de arrendamiento provider adapter must satisfy
    (`FakeAdapter` for dev/test, `SuraAdapter` for prod).

    Implementations receive the raw document bytes (desprendibles de pago,
    certificado laboral) only to forward them to the external provider —
    per spec.md's "Documentación de soporte no se persiste", no adapter may
    write them to disk, a database, or any other storage; they must be
    discarded once `contratar` returns.

    Raises `seguro_arrendamiento.domain.exceptions.ContratacionNoDisponible`
    when the provider cannot be reached (timeout/network/unexpected
    response) — never lets that failure surface as an unhandled exception,
    so the API layer can map it to an explicit "contratación no disponible"
    response instead of a 500.
    """

    async def contratar(
        self, *, cedula: str, documentos: list[bytes]
    ) -> ResultadoPoliza: ...


class PolizaArrendamientoRepositoryPort(Protocol):
    """Persistence contract for the `PolizaArrendamiento` aggregate.

    Per spec.md's "Documentación de soporte no se persiste", implementations
    must only ever receive/store the fields already on
    `PolizaArrendamiento` (estado, prima_mensual, vigencia, referencia
    externa) — never raw document bytes, which never reach this port in the
    first place.
    """

    async def guardar(self, poliza: PolizaArrendamiento) -> PolizaArrendamiento:
        """Insert a new `PolizaArrendamiento` and return it with `id` set."""
        ...

    async def listar_por_usuario(self, usuario_id: UUID) -> list[PolizaArrendamiento]:
        """Return every `PolizaArrendamiento` belonging to `usuario_id`
        (empty list if it has none)."""
        ...


class UsuarioIdentidadPort(Protocol):
    """Read-only view this domain uses to check `usuario.identidad_verificada`
    without depending on `usuarios`/`identidad` infrastructure directly —
    same rationale as `identidad.domain.ports.UsuarioIdentidadRepositoryPort`
    for `usuario.agencia_id`/`usuario.identidad_verificada`.

    This domain only ever reads the flag (design.md decisión 6, proposal.md
    Impact: "lectura de `usuario.identidad_verificada` ... sin modificarlo")
    — no method here can set it.
    """

    async def esta_verificado(self, usuario_id: UUID) -> bool:
        """Return the current value of `usuario.identidad_verificada`."""
        ...
