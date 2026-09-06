"""`FakeAdapter` — dev/test implementation of `ProveedorValidacionIdentidadPort`.

Per design.md decisión 4: always approves, so happy-path tests never need
to mock a variable proveedor response. Tests covering the rejection path
inject their own stub of `ProveedorValidacionIdentidadPort` instead of
touching this adapter (task 3.2 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`).
"""

from __future__ import annotations

import hashlib

from identidad.domain.ports import ResultadoValidacion


class FakeAdapter:
    """Always-approve implementation of `ProveedorValidacionIdentidadPort`,
    used as the default adapter in every environment until Truora
    credentials are configured (task 6.3)."""

    async def validar(
        self, *, cedula: str, imagen_frente: bytes, imagen_dorso: bytes
    ) -> ResultadoValidacion:
        """Discard the image bytes immediately (never persisted, per
        spec.md) and return an approved result with a `referencia_externa`
        deterministic on `cedula` — useful for assertions in integration
        tests."""
        referencia_externa = f"FAKE-{hashlib.sha256(cedula.encode('utf-8')).hexdigest()[:16]}"
        return ResultadoValidacion(aprobado=True, referencia_externa=referencia_externa)
