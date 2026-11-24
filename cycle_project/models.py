"""Воспроизводимые траектории; граф не сохраняется в памяти целиком."""

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class Trajectory:
    mu: int = 0
    lam: int = 1
    length: int | None = None
    work: int = 0

    def __post_init__(self):
        if self.mu < 0 or self.lam < 1 or self.work < 0:
            raise ValueError("Требуются mu >= 0, lambda >= 1 и work >= 0")
        if self.length is not None and self.length < 0:
            raise ValueError("Длина цепочки должна быть неотрицательной")

    @property
    def start(self):
        return None if self.length == 0 else 0

    def __call__(self, state):
        if self.work:
            payload = str(state).encode("ascii")
            for _ in range(self.work):
                payload = sha256(payload).digest()
        if self.length is not None:
            return None if state + 1 == self.length else state + 1
        return self.mu if state + 1 == self.mu + self.lam else state + 1


@dataclass(frozen=True)
class AgentState:
    phase: str
    data_ready: bool = False
    retries: int = 0


class ReportAgent:
    """Модель агента подготовки отчёта, без сети и платных API.

    loop: ошибка планировщика возвращает FETCH без изменения состояния.
    success: данные доступны сразу. retry: данные приходят после 3 попыток.
    """

    def __init__(self, scenario="loop"):
        if scenario not in ("loop", "success", "retry"):
            raise ValueError("Неизвестный сценарий агента")
        self.scenario = scenario

    @property
    def start(self):
        return AgentState("START")

    def __call__(self, state):
        if state.phase == "START":
            return AgentState("FETCH")
        if state.phase == "FETCH":
            if self.scenario == "loop":
                return AgentState("PLAN")
            if self.scenario == "retry" and state.retries < 2:
                return AgentState("FETCH", False, state.retries + 1)
            return AgentState("PLAN", True, state.retries)
        if state.phase == "PLAN":
            return (AgentState("VALIDATE", True, state.retries)
                    if state.data_ready else AgentState("FETCH"))
        if state.phase == "VALIDATE":
            return AgentState("WRITE", True, state.retries)
        if state.phase == "WRITE":
            return AgentState("DONE", True, state.retries)
        if state.phase == "DONE":
            return None
        raise ValueError("Неизвестная фаза")
