import hashlib
from .config import PSEUDONYM_SALT

def pseudonymize(value: str, salt: str = PSEUDONYM_SALT) -> str:
    digest = hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:10].upper()
    return f"STU-{digest}"
