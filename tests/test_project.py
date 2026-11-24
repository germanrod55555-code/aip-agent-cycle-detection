import random
import unittest

from cycle_project.algorithms import ALGORITHMS, floyd, brent, hashing, dictionary
from cycle_project.hash_table import HashTable
from cycle_project.models import Trajectory, ReportAgent, AgentState
from cycle_project.agent import run_agent


class CollisionKey:
    def __init__(self, value):
        self.value = value

    def __hash__(self):
        return 0

    def __eq__(self, other):
        return isinstance(other, CollisionKey) and self.value == other.value


class DetectionTests(unittest.TestCase):
    def check_model(self, model, expected):
        for name, fn in ALGORITHMS.items():
            with self.subTest(algorithm=name, model=model):
                r = fn(model.start, model)
                self.assertEqual((r.status, r.mu, r.lam, r.entry), expected)

    def test_self_loop(self):
        self.check_model(Trajectory(0, 1), ("cycle", 0, 1, 0))

    def test_tail_and_cycle(self):
        self.check_model(Trajectory(3, 4), ("cycle", 3, 4, 3))

    def test_long_prefix(self):
        self.check_model(Trajectory(10000, 1), ("cycle", 10000, 1, 10000))

    def test_long_cycle(self):
        self.check_model(Trajectory(0, 10000), ("cycle", 0, 10000, 0))

    def test_exhaustive_small_rho(self):
        for mu in range(25):
            for lam in range(1, 26):
                self.check_model(Trajectory(mu, lam), ("cycle", mu, lam, mu))

    def test_empty_and_finite(self):
        for n in range(101):
            self.check_model(Trajectory(length=n), ("terminated", None, None, None))

    def test_random_functional_graphs(self):
        rng = random.Random(20261115)
        for case in range(300):
            n = rng.randrange(1, 150)
            edges = [rng.choice([None] + list(range(n))) for _ in range(n)]
            start = rng.randrange(n)
            # Независимый простой оракул: линейный поиск в истории.
            history, current = [], start
            while current is not None and current not in history:
                history.append(current)
                current = edges[current]
            expected = (("terminated", None, None, None) if current is None else
                        ("cycle", history.index(current),
                         len(history)-history.index(current), current))
            for name, fn in ALGORITHMS.items():
                with self.subTest(case=case, algorithm=name):
                    r = fn(start, lambda s: edges[s])
                    self.assertEqual((r.status, r.mu, r.lam, r.entry), expected)

    def test_budget_is_not_no_cycle(self):
        for name, fn in ALGORITHMS.items():
            for budget in (0, 1, 7, 100):
                with self.subTest(name=name, budget=budget):
                    r = fn(0, lambda s: s+1, budget)
                    self.assertEqual(r.status, "limit")
                    self.assertEqual(r.calls, budget)
                    self.assertIsNone(r.mu)
                    self.assertIsNone(r.lam)

    def test_budget_exact_boundary(self):
        model = Trajectory(3, 4)
        for name, fn in ALGORITHMS.items():
            full = fn(0, model)
            self.assertEqual(fn(0, model, full.calls).status, "cycle")
            self.assertEqual(fn(0, model, full.calls-1).status, "limit")

    def test_successor_call_accounting(self):
        for name, fn in ALGORITHMS.items():
            for model in (Trajectory(3, 4), Trajectory(length=13)):
                calls = 0
                def step(s):
                    nonlocal calls
                    self.assertIsNotNone(s)
                    calls += 1
                    return model(s)
                result = fn(model.start, step)
                self.assertEqual(result.calls, calls)

    def test_invalid_limits_and_models(self):
        for fn in ALGORITHMS.values():
            with self.assertRaises(ValueError):
                fn(0, lambda s: s, -1)
        for params in ({"mu": -1}, {"lam": 0}, {"length": -1}, {"work": -1}):
            with self.assertRaises(ValueError):
                Trajectory(**params)

    def test_zero_state_is_not_terminal(self):
        self.check_model(Trajectory(0, 2), ("cycle", 0, 2, 0))


class HashTests(unittest.TestCase):
    def test_collisions_do_not_mean_equal(self):
        t = HashTable(2)
        for i in range(400):
            self.assertIsNone(t.remember(CollisionKey(i), i))
        for i in range(400):
            self.assertEqual(t.remember(CollisionKey(i), 999), i)
        self.assertEqual(t.size, 400)
        self.assertGreater(t.resizes, 0)

    def test_resize_preserves_first_index(self):
        t = HashTable(2)
        for i in range(5000):
            self.assertIsNone(t.remember(i, i*3))
        for i in range(5000):
            self.assertEqual(t.remember(i, -1), i*3)

    def test_negative_hash_and_capacity(self):
        t = HashTable()
        self.assertIsNone(t.remember(-7, 0))
        self.assertEqual(t.remember(-7, 1), 0)
        for capacity in (0, 1, 3, 5):
            with self.assertRaises(ValueError):
                HashTable(capacity)

    def test_cyclic_collision_states(self):
        def step(s):
            return CollisionKey(3 if s.value == 9 else s.value+1)
        for fn in (hashing, dictionary):
            r = fn(CollisionKey(0), step)
            self.assertEqual((r.mu, r.lam), (3, 7))


class AgentTests(unittest.TestCase):
    def test_loop_stops_before_repeat_action(self):
        model = ReportAgent("loop")
        out = run_agent(model)
        self.assertEqual((out["status"], out["mu"], out["lambda"]), ("cycle", 1, 2))
        self.assertEqual(out["actions"], 3)

    def test_success_and_retry(self):
        for scenario, actions in (("success", 6), ("retry", 8)):
            model = ReportAgent(scenario)
            out = run_agent(model)
            self.assertEqual(out["status"], "terminated")
            self.assertEqual(out["actions"], actions)
            for fn in ALGORITHMS.values():
                self.assertEqual(fn(model.start, model).status, "terminated")

    def test_complete_state_matters(self):
        self.assertNotEqual(AgentState("FETCH", False, 0),
                            AgentState("FETCH", False, 1))

    def test_agent_limits(self):
        self.assertEqual(run_agent(ReportAgent(), 0)["actions"], 0)
        self.assertEqual(run_agent(ReportAgent(), 2)["status"], "limit")
        self.assertEqual(run_agent(ReportAgent(), max_states=2)["status"], "limit")
        with self.assertRaises(ValueError):
            run_agent(ReportAgent(), -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
