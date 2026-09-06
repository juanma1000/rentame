"""`contratar_seguro_arrendamiento` use case.

Orchestrates the "Contratación de seguro de arrendamiento requiere
identidad verificada" and "Resultado modelado como póliza con estado
propio" requirements of
`openspec/changes/seguro-arrendamiento-inquilino/specs/seguro-arrendamiento/spec.md`
(tasks 3.1-3.3 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`).

This module only orchestrates: it checks `usuario.identidad_verificada` up
front (cheap, avoids a proveedor call when the gate fails), then delegates
to `PolizaArrendamiento` for every state transition — same pattern as
`identidad.application.iniciar_validacion_identidad`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from seguro_arrendamiento.domain.exceptions import IdentidadNoVerificada
from seguro_arrendamiento.domain.poliza_arrendamiento import PolizaArrendamiento
from seguro_arrendamiento.domain.ports import (
    PolizaArrendamientoRepositoryPort,
    ProveedorSeguroArrendamientoPort,
    UsuarioIdentidadPort,
)


@dataclass
class ContratarSeguroArrendamientoCommand:
    usuario_id: uuid.UUID
    cedula: str
    documentos: list[bytes]


async def contratar_seguro_arrendamiento(
    command: ContratarSeguroArrendamientoCommand,
    *,
    poliza_repository: PolizaArrendamientoRepositoryPort,
    usuario_identidad: UsuarioIdentidadPort,
    proveedor: ProveedorSeguroArrendamientoPort,
) -> PolizaArrendamiento:
    """Run a contratación de seguro de arrendamiento attempt for
    `command.usuario_id`.

    Raises `IdentidadNoVerificada` when the account does not have
    `identidad_verificada = True` — no `PolizaArrendamiento` is created and
    `proveedor.contratar` is never called (spec.md: "el sistema rechaza el
    intento sin llamar al proveedor externo").

    Otherwise, calls `proveedor.contratar` with the raw document bytes
    (which this use case never stores), records the outcome as a
    `PolizaArrendamiento` (`aprobada` or `rechazada`, always persisted for
    audit).
    """
    if not await usuario_identidad.esta_verificado(command.usuario_id):
        raise IdentidadNoVerificada(
            f"La cuenta {command.usuario_id} no tiene la identidad verificada"
        )

    resultado = await proveedor.contratar(
        cedula=command.cedula,
        documentos=command.documentos,
    )

    poliza = PolizaArrendamiento.solicitar(usuario_id=command.usuario_id)
    if resultado.aprobada:
        assert resultado.prima_mensual is not None
        assert resultado.vigencia_desde is not None
        assert resultado.vigencia_hasta is not None
        poliza.aprobar(
            prima_mensual=resultado.prima_mensual,
            vigencia_desde=resultado.vigencia_desde,
            vigencia_hasta=resultado.vigencia_hasta,
            referencia_externa=resultado.referencia_externa,
        )
    else:
        poliza.rechazar(referencia_externa=resultado.referencia_externa)

    return await poliza_repository.guardar(poliza)
