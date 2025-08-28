from cryptography.fernet import Fernet
import os

KEY_FILE = "vault/secret.key"

def generate_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)

def load_key():
    with open(KEY_FILE, "rb") as f:
        return f.read()

def encrypt_file(file_path, save_path):
    key = load_key()
    fernet = Fernet(key)

    with open(file_path, "rb") as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(save_path, "wb") as f:
        f.write(encrypted)

def decrypt_file(file_path, save_path):
    key = load_key()
    fernet = Fernet(key)

    with open(file_path, "rb") as f:
        data = f.read()

    decrypted = fernet.decrypt(data)

    with open(save_path, "wb") as f:
        f.write(decrypted)
