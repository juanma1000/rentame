"""`iniciar_validacion_identidad` use case.

Orchestrates the "Validación de identidad vía cédula colombiana",
"Resultado de validación contra proveedor externo" and "Una sola
validación exitosa por cuenta" requirements of
`openspec/changes/validacion-identidad-inquilino/specs/identidad/spec.md`
(tasks 3.1-3.3 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`).

This module only orchestrates: the "una sola validación aprobada" check
against the cached `Usuario.identidad_verificada` flag is done up front
(cheap, avoids a proveedor call for an already-verified account); the
`ValidacionIdentidad` invariant itself still lives in
`ValidacionIdentidad.iniciar` for callers that only have the full attempt
history (e.g. `ValidacionIdentidadRepositoryPort.listar_por_usuario`)
instead of the derived flag.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from identidad.domain.exceptions import IdentidadYaVerificada
from identidad.domain.ports import (
    ProveedorValidacionIdentidadPort,
    UsuarioIdentidadRepositoryPort,
    ValidacionIdentidadRepositoryPort,
)
from identidad.domain.validacion_identidad import ValidacionIdentidad


@dataclass
class IniciarValidacionIdentidadCommand:
    usuario_id: uuid.UUID
    cedula: str
    imagen_frente: bytes
    imagen_dorso: bytes


async def iniciar_validacion_identidad(
    command: IniciarValidacionIdentidadCommand,
    *,
    validacion_repository: ValidacionIdentidadRepositoryPort,
    usuario_repository: UsuarioIdentidadRepositoryPort,
    proveedor: ProveedorValidacionIdentidadPort,
) -> ValidacionIdentidad:
    """Run a validación de identidad attempt for `command.usuario_id`.

    Raises `IdentidadYaVerificada` when the account already has
    `identidad_verificada = True` — no `ValidacionIdentidad` is created and
    `proveedor.validar` is never called (spec.md: "el sistema rechaza el
    intento sin llamar al proveedor externo").

    Otherwise, calls `proveedor.validar` with the raw image bytes (which
    this use case never stores), records the outcome as a
    `ValidacionIdentidad` (`aprobado` or `rechazado`, always persisted for
    audit), and — only when approved — marks the account permanently
    verified.
    """
    if await usuario_repository.esta_verificado(command.usuario_id):
        raise IdentidadYaVerificada(
            f"La cuenta {command.usuario_id} ya tiene una validación de identidad aprobada"
        )

    resultado = await proveedor.validar(
        cedula=command.cedula,
        imagen_frente=command.imagen_frente,
        imagen_dorso=command.imagen_dorso,
    )

    validacion = ValidacionIdentidad.iniciar(
        usuario_id=command.usuario_id,
        cedula=command.cedula,
        validaciones_existentes=[],
    )
    if resultado.aprobado:
        validacion.aprobar(referencia_externa=resultado.referencia_externa)
    else:
        validacion.rechazar(referencia_externa=resultado.referencia_externa)

    validacion = await validacion_repository.guardar(validacion)

    if resultado.aprobado:
        await usuario_repository.marcar_verificado(command.usuario_id)

    return validacion
