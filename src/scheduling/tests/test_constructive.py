'''
Tests for constructive heuristics.
'''
import os
import unittest

from src.scheduling.instance.instance import Instance
from src.scheduling.optim.constructive import Greedy, NonDeterminist
from src.scheduling.tests.test_utils import TEST_FOLDER_DATA


class TestConstructive(unittest.TestCase):

    def setUp(self):
        self.instance_path = TEST_FOLDER_DATA + os.path.sep + "jsp1"

    def test_greedy_is_deterministic(self):
        inst1 = Instance.from_file(self.instance_path)
        inst2 = Instance.from_file(self.instance_path)

        sol1 = Greedy().run(inst1)
        sol2 = Greedy().run(inst2)

        key1 = [(op.operation_id, op.assigned_to, op.start_time) for op in sol1.all_operations]
        key2 = [(op.operation_id, op.assigned_to, op.start_time) for op in sol2.all_operations]
        self.assertEqual(key1, key2)
        self.assertTrue(sol1.is_feasible)

    def test_nondeterminist_seeded_is_reproducible(self):
        inst1 = Instance.from_file(self.instance_path)
        inst2 = Instance.from_file(self.instance_path)

        heur = NonDeterminist()
        sol1 = heur.run(inst1, {"seed": 7})
        sol2 = heur.run(inst2, {"seed": 7})

        key1 = [(op.operation_id, op.assigned_to, op.start_time) for op in sol1.all_operations]
        key2 = [(op.operation_id, op.assigned_to, op.start_time) for op in sol2.all_operations]
        self.assertEqual(key1, key2)

    def test_nondeterminist_without_seed_varies(self):
        # Small instance can occasionally produce same schedule by chance, so repeat a few times.
        signatures = set()
        for _ in range(5):
            inst = Instance.from_file(self.instance_path)
            sol = NonDeterminist().run(inst)
            signatures.add(tuple((op.operation_id, op.assigned_to, op.start_time) for op in sol.all_operations))

        self.assertGreaterEqual(len(signatures), 2)


if __name__ == "__main__":
    unittest.main()

