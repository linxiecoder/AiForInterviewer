"""Auth domain services."""

from app.domain.auth.entities import CurrentActor, UserAccount


def actor_from_user(account: UserAccount) -> CurrentActor:
    return CurrentActor(
        actor_id=account.user_id,
        owner_id=account.owner_id,
        roles=account.roles,
        email_normalized=account.email_normalized,
        display_name=account.display_name,
    )
