"""Флойд, Брент, собственное хеширование и библиотечный эталон.

Контракт: successor(s) — чистая детерминированная функция. None означает
завершение. Состояния неизменяемы; равенство отражает все данные,
влияющие на следующий шаг. Для хеширования дополнительно нужен hash().
"""

from dataclasses import dataclass
from .hash_table import HashTable


@dataclass(frozen=True)
class Result:
    status: str
    mu: int | None = None
    lam: int | None = None
    entry: object = None
    calls: int = 0
    comparisons: int | None = None
    stored_states: int = 0


class _BudgetExceeded(Exception):
    pass


class _Runner:
    __slots__ = ("successor", "limit", "calls", "comparisons")

    def __init__(self, successor, max_calls):
        if max_calls < 0:
            raise ValueError("Лимит вызовов не может быть отрицательным")
        self.successor, self.limit = successor, max_calls
        self.calls, self.comparisons = 0, 0

    def step(self, state):
        if state is None:
            return None
        if self.calls >= self.limit:
            raise _BudgetExceeded
        self.calls += 1
        return self.successor(state)

    def equal(self, a, b):
        self.comparisons += 1
        return a == b

    def result(self, status, mu=None, lam=None, entry=None):
        return Result(status, mu, lam, entry, self.calls, self.comparisons)


def floyd(start, successor, max_calls=10_000_000):
    """Два указателя; после встречи восстановить начало и длину цикла."""
    r = _Runner(successor, max_calls)
    if start is None:
        return r.result("terminated")
    try:
        slow = r.step(start)
        fast = r.step(r.step(start))
        while slow is not None and fast is not None:
            if r.equal(slow, fast):
                break
            slow = r.step(slow)
            fast = r.step(r.step(fast))
        else:
            return r.result("terminated")
        mu, slow = 0, start
        while not r.equal(slow, fast):
            slow, fast = r.step(slow), r.step(fast)
            mu += 1
        entry = slow
        lam, fast = 1, r.step(entry)
        while not r.equal(entry, fast):
            fast = r.step(fast)
            lam += 1
        return r.result("cycle", mu, lam, entry)
    except _BudgetExceeded:
        return r.result("limit")


def brent(start, successor, max_calls=10_000_000):
    """Опорное состояние и блоки длины 1, 2, 4, 8 и так далее."""
    r = _Runner(successor, max_calls)
    if start is None:
        return r.result("terminated")
    try:
        power = lam = 1
        anchor, current = start, r.step(start)
        while current is not None:
            if r.equal(anchor, current):
                break
            if power == lam:
                anchor = current
                power *= 2
                lam = 0
            current = r.step(current)
            lam += 1
        else:
            return r.result("terminated")
        slow = fast = start
        for _ in range(lam):
            fast = r.step(fast)
        mu = 0
        while not r.equal(slow, fast):
            slow, fast = r.step(slow), r.step(fast)
            mu += 1
        return r.result("cycle", mu, lam, slow)
    except _BudgetExceeded:
        return r.result("limit")


def hashing(start, successor, max_calls=10_000_000):
    """Один проход с собственной таблицей первых появлений."""
    r = _Runner(successor, max_calls)
    table = HashTable()
    current, index = start, 0
    try:
        while current is not None:
            first = table.remember(current, index)
            if first is not None:
                return Result("cycle", first, index-first, current,
                              r.calls, None, table.size)
            current = r.step(current)
            index += 1
        return Result("terminated", calls=r.calls,
                      stored_states=table.size)
    except _BudgetExceeded:
        return Result("limit", calls=r.calls, stored_states=table.size)


def dictionary(start, successor, max_calls=10_000_000):
    """Библиотечная база сравнения: встроенный словарь Python."""
    r = _Runner(successor, max_calls)
    seen = {}
    current, index = start, 0
    try:
        while current is not None:
            first = seen.get(current)
            if first is not None:
                return Result("cycle", first, index-first, current,
                              r.calls, None, len(seen))
            seen[current] = index
            current = r.step(current)
            index += 1
        return Result("terminated", calls=r.calls, stored_states=len(seen))
    except _BudgetExceeded:
        return Result("limit", calls=r.calls, stored_states=len(seen))


ALGORITHMS = {"floyd": floyd, "brent": brent,
              "hash": hashing, "dict": dictionary}
