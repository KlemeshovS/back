from __future__ import annotations

from base64 import b64decode, b64encode
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from secrets import token_bytes, token_urlsafe

PBKDF2_ITERATIONS = 600_000


def generate_admin_access_token() -> str:
    return f"adm_{token_urlsafe(32)}"


def hash_admin_access_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    encoded_salt = b64encode(salt).decode()
    encoded_digest = b64encode(digest).decode()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    salt = b64decode(salt_b64.encode())
    expected_digest = b64decode(digest_b64.encode())
    actual_digest = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        int(iterations),
    )
    return compare_digest(actual_digest, expected_digest)
