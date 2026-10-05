import hashlib
import secrets

from pwdlib import PasswordHash

COOKIE_NAME = "fsp_session"
password_hasher = PasswordHash.recommended()
# The same expensive verification runs for nonexistent accounts.
DUMMY_HASH = password_hasher.hash(secrets.token_urlsafe(32))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)
