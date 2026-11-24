"""Воспроизводимое сравнение. Запуск: python benchmark.py --out results."""

import argparse
import csv
import gc
import json
import os
import platform
import random
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

from cycle_project.algorithms import ALGORITHMS
from cycle_project.models import Trajectory


def cases():
    for n in (100, 1000, 10000, 100000):
        for ratio in (0, 0.5, 0.9):
            mu = int(n * ratio)
            yield f"rho_{n}_{int(ratio*100)}", Trajectory(mu, n-mu)
        yield f"chain_{n}", Trajectory(length=n)
    for ratio in (0, 0.5, 0.9):
        mu = int(1000 * ratio)
        yield f"costly_1000_{int(ratio*100)}", Trajectory(mu, 1000-mu, work=50)


def run(out, repeats=7):
    if repeats < 3:
        raise ValueError("Для сравнения нужно не меньше трёх повторов")
    out.mkdir(parents=True, exist_ok=True)
    raw, summary = [], []
    rng = random.Random(20261115)
    for case, model in cases():
        timings = {name: [] for name in ALGORITHMS}
        reference = ("terminated", None, None) if model.length is not None else (
            "cycle", model.mu, model.lam)
        for name, fn in ALGORITHMS.items():
            r = fn(model.start, model)  # Прогрев отдельно от измерений.
            assert (r.status, r.mu, r.lam) == reference
        for repeat in range(repeats):
            order = list(ALGORITHMS)
            rng.shuffle(order)
            for name in order:
                gc.collect()
                enabled = gc.isenabled()
                gc.disable()
                try:
                    t0 = time.perf_counter_ns()
                    r = ALGORITHMS[name](model.start, model)
                    elapsed = (time.perf_counter_ns()-t0) / 1_000_000
                finally:
                    if enabled:
                        gc.enable()
                assert (r.status, r.mu, r.lam) == reference
                timings[name].append(elapsed)
                raw.append({"case": case, "algorithm": name,
                            "repeat": repeat+1, "ms": elapsed,
                            "calls": r.calls, "status": r.status})
        for name, fn in ALGORITHMS.items():
            gc.collect()
            tracemalloc.start()
            try:
                r = fn(model.start, model)
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            q = statistics.quantiles(timings[name], n=4, method="inclusive")
            summary.append({"case": case, "algorithm": name,
                            "n": model.length if model.length is not None else model.mu+model.lam,
                            "mu": model.mu if model.length is None else None,
                            "lambda": model.lam if model.length is None else None,
                            "work": model.work, "status": r.status,
                            "median_ms": statistics.median(timings[name]),
                            "q1_ms": q[0], "q3_ms": q[2],
                            "min_ms": min(timings[name]), "max_ms": max(timings[name]),
                            "peak_bytes": peak, "calls": r.calls,
                            "stored_states": r.stored_states})
        print(f"Готово: {case}", flush=True)
    for filename, rows in (("raw_timings.csv", raw), ("summary.csv", summary)):
        with (out/filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    environment = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                   "python": sys.version.split()[0], "implementation": platform.python_implementation(),
                   "platform": platform.platform(), "processor": platform.processor(),
                   "logical_cpu_count": os.cpu_count(), "repeats": repeats,
                   "seed": 20261115, "cases": 19, "algorithms": 4,
                   "timer": "perf_counter_ns", "gc_during_timing": False,
                   "memory": "peak traced allocations in a separate tracemalloc run",
                   "costly_transition": "50 SHA-256 digests per successor call"}
    (out/"environment.json").write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--repeats", type=int, default=7)
    args = parser.parse_args()
    run(args.out, args.repeats)
