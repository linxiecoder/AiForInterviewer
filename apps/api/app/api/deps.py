"""FastAPI dependency placeholders for F5 owner/auth boundary."""

from dataclasses import dataclass

from fastapi import Header


@dataclass(frozen=True)
class CurrentActor:
    actor_id: str
    owner_id: str


def require_current_actor(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> CurrentActor:
    actor_id = (x_user_id or "usr_f5_m0_placeholder").strip()
    return CurrentActor(actor_id=actor_id, owner_id=actor_id)

