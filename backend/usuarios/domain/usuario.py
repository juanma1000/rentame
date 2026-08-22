"""`Usuario` aggregate root: account identity, credentials and role.

Business rules come from `openspec/changes/hu-008/specs/usuarios/spec.md`
(Requirements: "Registro como propietario o inquilino", "Registro como
agente requiere resolver el paso de agencia", "Rol único y fijo por cuenta")
and `design.md` decisión 2 (bcrypt hashing, `password_hash` never exposed as
plaintext).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import bcrypt


@dataclass
class Usuario:
    """A registered account, identified by email and authenticated by
    password.

    Instances must be built through `Usuario.crear`, which hashes the
    plaintext password with bcrypt before storing it — there is no
    plaintext `password` attribute anywhere on this entity.

    `id` is `None` until a repository assigns one on insert — same pattern
    as `Agencia.crear`/`Inmueble.crear`.
    """

    email: str
    password_hash: str
    nombre: str
    rol: str
    id: uuid.UUID | None = None
    agencia_id: uuid.UUID | None = None

    @classmethod
    def crear(cls, *, email: str, password: str, nombre: str, rol: str) -> Usuario:
        """Hash `password` with bcrypt and create a new `Usuario`.

        `rol` is fixed permanently at creation time (spec.md: "Rol único y
        fijo por cuenta") — there is no method to change it afterwards.
        """
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        return cls(email=email, password_hash=password_hash, nombre=nombre, rol=rol)

    def verificar_password(self, password: str) -> bool:
        """Return `True` when `password` matches this account's stored hash.

        Returns `False` (never raises) when `password_hash` is empty or not a
        well-formed bcrypt hash — e.g. accounts created directly in the
        database before this domain existed — so a login attempt against
        them fails like a wrong password instead of crashing with a 500.
        """
        try:
            return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))
        except ValueError:
            return False
