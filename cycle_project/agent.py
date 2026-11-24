"""Однопроходный предохранитель перед выполнением очередного действия."""

from dataclasses import asdict
from .hash_table import HashTable


def run_agent(agent, max_actions=100, max_states=10000):
    if max_actions < 0 or max_states < 1:
        raise ValueError("Некорректный лимит агента")
    seen = HashTable()
    state, actions = agent.start, 0
    trace = []  # Только журнал интерфейса, не структура детектора.
    while state is not None:
        first = seen.remember(state, actions)
        trace.append({"step": actions, **asdict(state)})
        if first is not None:
            return {"status": "cycle", "actions": actions, "mu": first,
                    "lambda": actions-first, "trace": trace}
        if seen.size >= max_states or actions >= max_actions:
            return {"status": "limit", "actions": actions, "trace": trace}
        # В реальном пайплайне здесь выполняется ровно одно действие.
        state = agent(state)
        actions += 1
    return {"status": "terminated", "actions": actions, "trace": trace}
