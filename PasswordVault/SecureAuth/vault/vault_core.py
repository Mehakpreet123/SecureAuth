from collections import defaultdict
from typing import DefaultDict, List
from .encryption import AESCipher
from .trie import Trie
from .logger import ActivityLogger
from .utils import generate_password

class PasswordVault:
    def __init__(self, master_password: str):
        self.cipher = AESCipher(master_password)
        self.store: DefaultDict[str, dict[str, List[str]]] = defaultdict(dict)
        self.trie = Trie()
        self.logger = ActivityLogger()

    # ---------- CRUD ----------
    def add(self, uid: str, service: str, pwd_plain: str):
        enc = self.cipher.encrypt(pwd_plain)
        self.store[uid].setdefault(service, []).append(enc)
        self.trie.insert(service)
        self.logger.log(uid, "ADD", service)

    def update(self, uid: str, service: str, new_pwd: str):
        if service not in self.store[uid]:
            raise KeyError("Service not found")
        self.add(uid, service, new_pwd)
        self.logger.log(uid, "UPDATE", service)

    def get(self, uid: str, service: str) -> str | None:
        stack = self.store[uid].get(service)
        if not stack:
            return None
        self.logger.log(uid, "VIEW", service)
        return self.cipher.decrypt(stack[-1])

    def rollback(self, uid: str, service: str) -> str | None:
        stack = self.store[uid].get(service, [])
        if len(stack) < 2:
            return None
        stack.pop()
        self.logger.log(uid, "ROLLBACK", service)
        return self.cipher.decrypt(stack[-1])

    # ---------- Helpers ----------
    def search(self, prefix: str) -> list[str]:
        return self.trie.starts_with(prefix)

    def new_password(self, **kw):
        return generate_password(**kw)
