import secrets
import hashlib


def generate_2fa_code(length: int) -> str:
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()
