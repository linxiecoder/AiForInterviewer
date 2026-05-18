"""Password hashing adapters for the F5 auth baseline."""

from __future__ import annotations

from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
import hashlib
import hmac
import secrets


class Pbkdf2PasswordHasher:
    algorithm = "pbkdf2_sha256"

    def __init__(self, *, iterations: int = 120_000, salt_bytes: int = 16) -> None:
        self.iterations = iterations
        self.salt_bytes = salt_bytes

    def hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(self.salt_bytes)
        digest = self._digest(password, salt, self.iterations)
        salt_b64 = b64encode(salt).decode("ascii")
        digest_b64 = b64encode(digest).decode("ascii")
        return f"{self.algorithm}${self.iterations}${salt_b64}${digest_b64}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations_raw, salt_b64, digest_b64 = password_hash.split("$", 3)
            if algorithm != self.algorithm:
                return False
            iterations = int(iterations_raw)
            salt = b64decode(salt_b64.encode("ascii"), validate=True)
            expected_digest = b64decode(digest_b64.encode("ascii"), validate=True)
        except (BinasciiError, ValueError, TypeError):
            return False

        actual_digest = self._digest(password, salt, iterations)
        return hmac.compare_digest(actual_digest, expected_digest)

    @staticmethod
    def _digest(password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
