"""Командный интерфейс: python -m cycle_project --help."""

import argparse
import json
from dataclasses import asdict
from .algorithms import ALGORITHMS
from .models import Trajectory, ReportAgent
from .agent import run_agent


def main():
    parser = argparse.ArgumentParser(description="Обнаружение циклов Флойдом и Брентом")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("compare", help="Сравнить детекторы на одной траектории")
    p.add_argument("--mu", type=int, default=3)
    p.add_argument("--lam", type=int, default=4)
    p.add_argument("--length", type=int, default=None,
                   help="Конечная цепочка указанной длины вместо цикла")
    p.add_argument("--budget", type=int, default=10_000_000)
    p = sub.add_parser("agent", help="Продемонстрировать автоматическую остановку")
    p.add_argument("--scenario", choices=("loop", "success", "retry"), default="loop")
    p.add_argument("--budget", type=int, default=100)
    sub.add_parser("web", help="Открыть локальный демонстрационный интерфейс")
    args = parser.parse_args()
    try:
        if args.command == "compare":
            model = Trajectory(args.mu, args.lam, args.length)
            result = {name: asdict(fn(model.start, model, args.budget))
                      for name, fn in ALGORITHMS.items()}
        elif args.command == "agent":
            result = run_agent(ReportAgent(args.scenario), args.budget)
        else:
            from .web import serve
            serve()
            return
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
