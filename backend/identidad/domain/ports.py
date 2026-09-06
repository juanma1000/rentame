"""Outbound ports for the `identidad` domain.

`Protocol`s (structural typing), same rationale as `agencias/domain/ports.py`
and `inmuebles/domain/ports.py` — adapters only need to match the shape, not
inherit from a common base. Methods are `async` for the same reason: the
project's persistence layer and any HTTP-backed adapter are built on async
I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from identidad.domain.validacion_identidad import ValidacionIdentidad


@dataclass
class ResultadoValidacion:
    """Outcome of a single call to a `ProveedorValidacionIdentidadPort`
    adapter.

    `aprobado` is `True`/`False` for a definitive answer from the proveedor;
    `referencia_externa` is the proveedor's own tracking id for that check
    (kept so a disputed result can be re-consulted against the proveedor
    later, per design.md's "Trade-off" on not persisting images).
    """

    aprobado: bool
    referencia_externa: str


class ProveedorValidacionIdentidadPort(Protocol):
    """Contract every identity-verification provider adapter must satisfy
    (`FakeAdapter` for dev/test, `TruoraAdapter` for prod).

    Implementations receive the raw document image bytes only to forward
    them to the external provider — per spec.md's "Imágenes del documento
    no se persisten", no adapter may write them to disk, a database, or any
    other storage; they must be discarded once `validar` returns.

    Raises `identidad.domain.exceptions.ValidacionNoDisponible` when the
    provider cannot be reached (timeout/network/unexpected response) —
    never lets that failure surface as an unhandled exception, so the API
    layer can map it to an explicit "validación no disponible" response
    instead of a 500.
    """

    async def validar(
        self, *, cedula: str, imagen_frente: bytes, imagen_dorso: bytes
    ) -> ResultadoValidacion: ...


class ValidacionIdentidadRepositoryPort(Protocol):
    """Persistence contract for the `ValidacionIdentidad` aggregate.

    Per spec.md's "Imágenes del documento no se persisten", implementations
    must only ever receive/store the fields already on `ValidacionIdentidad`
    (cedula as text, estado, fecha, referencia_externa) — never raw image
    bytes, which never reach this port in the first place.
    """

    async def guardar(self, validacion: ValidacionIdentidad) -> ValidacionIdentidad:
        """Insert a new `ValidacionIdentidad` and return it with `id` set."""
        ...

    async def listar_por_usuario(self, usuario_id: UUID) -> list[ValidacionIdentidad]:
        """Return every `ValidacionIdentidad` attempt belonging to `usuario_id`
        (empty list if it has none), used to enforce the "una sola
        validación aprobada por cuenta" invariant (`ValidacionIdentidad.iniciar`).
        """
        ...


class UsuarioIdentidadRepositoryPort(Protocol):
    """Persistence contract this domain uses to read/write
    `Usuario.identidad_verificada` without depending on `usuarios`
    infrastructure directly — same rationale as `agencias.domain.ports.
    UsuarioAgenciaRepositoryPort` for `usuario.agencia_id`.
    """

    async def esta_verificado(self, usuario_id: UUID) -> bool:
        """Return the current value of `usuario.identidad_verificada`."""
        ...

    async def marcar_verificado(self, usuario_id: UUID) -> None:
        """Set `usuario.identidad_verificada = True` for `usuario_id`.

        Permanent per spec.md/design.md decisión 5 — there is no method to
        revert it.
        """
        ...
