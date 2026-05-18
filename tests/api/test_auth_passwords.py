from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.infrastructure.security.stores import InMemorySessionStore, digest_session_token
from app.domain.auth.entities import CurrentActor
from app.domain.shared.clock import utc_now


def test_pbkdf2_password_hash_verifies_and_does_not_store_plaintext() -> None:
    hasher = Pbkdf2PasswordHasher(iterations=1_000)

    password_hash = hasher.hash_password("correct horse battery staple")

    assert password_hash.startswith("pbkdf2_sha256$")
    assert "correct horse battery staple" not in password_hash
    assert hasher.verify_password("correct horse battery staple", password_hash)
    assert not hasher.verify_password("wrong password", password_hash)


def test_pbkdf2_password_hash_rejects_malformed_hash() -> None:
    hasher = Pbkdf2PasswordHasher(iterations=1_000)

    assert not hasher.verify_password("password", "not-a-valid-hash")


def test_in_memory_session_store_keeps_only_digest() -> None:
    store = InMemorySessionStore()
    actor = CurrentActor(
        actor_id="usr_test",
        owner_id="usr_test",
        roles=("user",),
        email_normalized="user@example.com",
        display_name="Test User",
    )

    issued = store.issue_session(actor, utc_now())

    assert issued.session.session_digest == digest_session_token(issued.raw_token)
    assert issued.raw_token != issued.session.session_digest
