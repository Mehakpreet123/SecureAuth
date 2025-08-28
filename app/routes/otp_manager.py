import pyotp
import uuid
import re


URI_RE = re.compile(r"^otpauth://", re.IGNORECASE)

def ingest_input(raw_text: str, fallback_label: str | None = None):
    """
    Accepts either:
    - full otpauth URI         -> returns (label, secret)
    - raw base32 secret string -> returns (label, secret)
    """
    raw_text = raw_text.strip()

    # If URI provided
    if URI_RE.match(raw_text):
        totp = pyotp.parse_uri(raw_text)
        return totp.name, totp.secret

    # If raw secret, fallback label is required
    if not fallback_label:
        raise ValueError("Label is required when providing a raw secret.")

    # Validate secret
    try:
        _ = pyotp.TOTP(raw_text).now()
    except Exception:
        raise ValueError("Invalid Base32 secret format.")

    return fallback_label, raw_text

def extract_issuer(label):
    if ':' in label:
        return label.split(':')[0]
    return "Unknown"

import uuid

def add_otp_entry(label, secret, user_id, db):
    otp_secret_id = uuid.uuid4().hex
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO otp_secrets (otp_secret_id, secret_key, assigned_to, purpose, label)
        VALUES (%s, %s, %s, %s, %s)
    """, (otp_secret_id, secret, user_id, 'auth_app', label))
    db.commit()

def generate_otp(secret):
    try:
        totp = pyotp.TOTP(secret)
        return totp.now()
    except Exception:
        return "Invalid Secret"

