import time
from werkzeug.security import check_password_hash
from DSA.hashmap import user_db
from collections import deque

MAX_ATTEMPTS = 5   
TIME_WINDOW = 60   

def login_user(username, password):
    """Validates login with brute-force prevention."""
    if username not in user_db:
        return False

    user_data = user_db[username]
    attempts = user_data["attempts"]
    current_time = time.time()

    while attempts and current_time - attempts[0] > TIME_WINDOW:
        attempts.popleft()

  
    if len(attempts) >= MAX_ATTEMPTS:
        return False

    if check_password_hash(user_data["password"], password):
        attempts.clear()  
        return True
    else:
        attempts.append(current_time)
        return False
