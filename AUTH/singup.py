from werkzeug.security import generate_password_hash
from DSA.hashmap import user_db

def signup_user(username, password):
    """Registers a new user if not already present."""
    if username in user_db:  # Check if already exists (O(1) lookup)
        return False

    hashed_password = generate_password_hash(password)
    user_db[username] = {
        "password": hashed_password,
        "attempts": deque()  # Track failed attempts for brute-force prevention
    }
    return True
