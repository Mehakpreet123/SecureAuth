class _Node:
    __slots__ = ("children", "end", "refs")
    def __init__(self):
        self.children = {}
        self.end = False
        self.refs = []

class Trie:
    def __init__(self):
        self.root = _Node()

    def insert(self, word: str):
        node = self.root
        for ch in word.lower():
            node = node.children.setdefault(ch, _Node())
        node.end = True
        node.refs.append(word)

    def starts_with(self, prefix: str) -> list[str]:
        node = self.root
        for ch in prefix.lower():
            if ch not in node.children:
                return []
            node = node.children[ch]
        return self._collect(node)

    def _collect(self, node: _Node) -> list[str]:
        out = []
        if node.end:
            out.extend(node.refs)
        for child in node.children.values():
            out.extend(self._collect(child))
        return out
