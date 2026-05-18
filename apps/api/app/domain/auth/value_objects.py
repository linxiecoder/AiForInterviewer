"""Auth domain value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleScope:
    roles: tuple[str, ...]

    def has_role(self, role: str) -> bool:
        return role in self.roles


@dataclass(frozen=True)
class OwnerScope:
    actor_id: str
    owner_id: str
    roles: tuple[str, ...]

    def can_access_owner(self, owner_id: str) -> bool:
        return self.owner_id == owner_id or "admin" in self.roles
