from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib

def get_key(password: str, salt: bytes):
    # Derive a 32-byte AES key from the password and salt
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return key

 
def encrypt_file(filepath, password):
    with open(filepath, 'rb') as f:
        data = f.read()

    salt = get_random_bytes(16)
    key = get_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    encrypted_path = filepath + ".enc"
    with open(encrypted_path, 'wb') as f:
        f.write(salt + cipher.nonce + tag + ciphertext)

    return encrypted_path



def decrypt_file(filepath, password):
    with open(filepath, 'rb') as f:
        file_data = f.read()

    salt = file_data[:16]
    nonce = file_data[16:32]
    tag = file_data[32:48]
    ciphertext = file_data[48:]

    key = get_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce)
    data = cipher.decrypt_and_verify(ciphertext, tag)

    decrypted_path = filepath.replace('.enc', '')
    with open(decrypted_path, 'wb') as f:
        f.write(data)

    return decrypted_path



