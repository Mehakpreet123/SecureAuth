from collections import deque

# In-memory user database (like a HashMap)
user_db = {}
# Example structure after signup:
# {
#   "gautham": {
#       "password": "<hashed_password>",
#       "attempts": deque([timestamp1, timestamp2])
#   }
# }
