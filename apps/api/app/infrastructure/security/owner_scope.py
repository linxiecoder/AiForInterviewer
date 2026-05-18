"""Owner scope adapter placeholder for F5 auth foundation."""

from app.domain.auth.entities import CurrentActor
from app.domain.auth.value_objects import OwnerScope


class OwnerScopeAdapter:
    def from_actor(self, actor: CurrentActor) -> OwnerScope:
        return OwnerScope(actor_id=actor.actor_id, owner_id=actor.owner_id, roles=actor.roles)

    def can_access_owner(self, actor: CurrentActor, owner_id: str) -> bool:
        return self.from_actor(actor).can_access_owner(owner_id)
