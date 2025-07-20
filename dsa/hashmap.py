class User:
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
        self.entries = {}  # later for 2FA entries

class HashMap:
    def __init__(self, size=100):
        self.size = size
        self.map = [[] for _ in range(size)]

    def _hash(self, key):
        return sum(ord(c) for c in key) % self.size

    def put(self, key, value):
        index = self._hash(key)
        for i, (k, _) in enumerate(self.map[index]):
            if k == key:
                self.map[index][i] = (key, value)
                return
        self.map[index].append((key, value))

    def get(self, key):
        index = self._hash(key)
        for k, v in self.map[index]:
            if k == key:
                return v
        return None

    def contains(self, key):
        return self.get(key) is not None

    def __contains__(self, key):
        return self.contains(key)
    
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.put(key, value)


