import bcrypt
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# =========================
# Password Hashing (bcrypt)
# =========================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ==============================
# PBKDF2 Key Derivation (for RSA)
# ==============================
def derive_key_from_password(password: str, salt: bytes, iterations: int = 210000) -> bytes:
    """
    Derive a 32-byte key from the user's password using PBKDF2-HMAC-SHA256.
    This key is used to encrypt/decrypt the user's private RSA key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode("utf-8"))


def encode_salt(salt: bytes) -> str:
    """Convert raw salt to a safe base64 string for DB storage."""
    return base64.b64encode(salt).decode("utf-8")

def decode_salt(salt_b64: str) -> bytes:
    """Convert base64-encoded salt back to raw bytes."""
    return base64.b64decode(salt_b64.encode("utf-8"))
