from hashlib import sha256
from secrets import token_urlsafe


def generate_access_token() -> str:
    return f"rt_{token_urlsafe(32)}"


def hash_access_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
