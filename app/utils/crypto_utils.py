from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os, base64, json

# ======================================================
# ---- Fernet (already used for vault encryption) ----
# ======================================================

# Generate only once and store securely!
def generate_key():
    return Fernet.generate_key()

# For demo: load key from file (store securely in prod!)
def load_key():
    with open("secret.key", "rb") as key_file:
        return key_file.read()

# Save key only once
def save_key(key):
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Encrypt password (Fernet)
def encrypt_password(password, key):
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

# Decrypt password (Fernet)
def decrypt_password(token, key):
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()


# ======================================================
# ---- Hybrid Crypto for Secure Sharing (AES + RSA) ----
# ======================================================

def b64e(b): return base64.b64encode(b).decode("utf-8")
def b64d(s): return base64.b64decode(s.encode("utf-8"))

# ----- RSA keypair -----
def generate_rsa_keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    pub = priv.public_key()
    return priv, pub

def serialize_public_key(pub):
    return pub.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

def serialize_private_key_encrypted(priv, passkey: bytes):
    return priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(passkey)
    ).decode()

def load_public_key(pem: str):
    return serialization.load_pem_public_key(pem.encode())

def load_private_key_encrypted(pem_enc: str, passkey: bytes):
    return serialization.load_pem_private_key(pem_enc.encode(), password=passkey)

def load_private_key(pem, password=None):
    return serialization.load_pem_private_key(
        pem.encode(),
        password=password.encode() if password else None,
    )


# ----- AES-GCM helpers -----
def aesgcm_encrypt(plaintext: bytes):
    key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return key, nonce, ct

def aesgcm_decrypt(key: bytes, nonce: bytes, ct: bytes):
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)


# ----- RSA wrap/unwrap for the AES key -----
def rsa_wrap_key(pub, aes_key: bytes):
    wrapped = pub.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(),
                     label=None)
    )
    return wrapped

def rsa_unwrap_key(priv, wrapped: bytes):
    return priv.decrypt(
        wrapped,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(),
                     label=None)
    )

# ----- package/unpackage share token -----
def pack_share_token(wrapped_key: bytes, nonce: bytes, ct: bytes):
    payload = {
        "wk": b64e(wrapped_key),
        "n":  b64e(nonce),
        "c":  b64e(ct),
    }
    return json.dumps(payload)

import json
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

def unpack_share_token(token_json, private_key):
    """
    Unpack the shared JSON token and decrypt the password.
    """
    data = json.loads(token_json)

    wrapped = base64.b64decode(data["wk"])   # match "wk"
    nonce   = base64.b64decode(data["n"])    # match "n"
    ct      = base64.b64decode(data["c"])    # match "c"

    # 🔑 Unwrap AES key with receiver’s private RSA key
    aes_key = private_key.decrypt(
        wrapped,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 🔓 Decrypt ciphertext with AESGCM
    aesgcm = AESGCM(aes_key)
    plaintext = aesgcm.decrypt(nonce, ct, None)

    return plaintext.decode()


