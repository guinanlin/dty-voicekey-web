import hashlib
import secrets


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_pair_id() -> str:
    return f"pair_{secrets.token_hex(6)}"


def generate_pair_token() -> str:
    return f"pt_{secrets.token_urlsafe(24)}"


def generate_agent_token() -> str:
    return f"at_{secrets.token_urlsafe(24)}"


def verify_token(token: str, token_hash: str) -> bool:
    return hash_token(token) == token_hash
