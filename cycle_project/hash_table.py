"""Хеш-таблица с цепочками, без dict, set и list в ядре хранения.

Массив ссылок ctypes имеет фиксированную ёмкость. Узлы цепочек,
разрешение коллизий и перенос при расширении реализованы явно.
"""

from ctypes import py_object


class _Node:
    __slots__ = ("key", "index", "code", "next")

    def __init__(self, key, index, code, next_node):
        self.key, self.index = key, index
        self.code, self.next = code, next_node


class HashTable:
    """Хранит номер первого появления неизменяемого состояния."""

    __slots__ = ("_buckets", "capacity", "size", "resizes", "probes")

    def __init__(self, capacity=16):
        if capacity < 2 or capacity & (capacity - 1):
            raise ValueError("Ёмкость должна быть степенью двойки, не меньше 2")
        self.capacity, self.size = capacity, 0
        self.resizes, self.probes = 0, 0
        self._buckets = self._allocate(capacity)

    @staticmethod
    def _allocate(capacity):
        buckets = (py_object * capacity)()
        for i in range(capacity):
            buckets[i] = None
        return buckets

    def _grow(self):
        new_capacity = self.capacity * 2
        buckets = self._allocate(new_capacity)
        for i in range(self.capacity):
            node = self._buckets[i]
            while node is not None:
                following = node.next
                slot = node.code & (new_capacity - 1)
                node.next = buckets[slot]
                buckets[slot] = node
                node = following
        self._buckets, self.capacity = buckets, new_capacity
        self.resizes += 1

    def remember(self, key, index):
        """Вернуть прежний индекс или сохранить новый ключ и вернуть None."""
        code = hash(key)
        slot = code & (self.capacity - 1)
        node = self._buckets[slot]
        while node is not None:
            self.probes += 1
            # Совпадения хеша недостаточно: требуется равенство состояний.
            if node.code == code and node.key == key:
                return node.index
            node = node.next
        if (self.size + 1) * 4 > self.capacity * 3:
            self._grow()
            slot = code & (self.capacity - 1)
        self._buckets[slot] = _Node(key, index, code, self._buckets[slot])
        self.size += 1
        return None
