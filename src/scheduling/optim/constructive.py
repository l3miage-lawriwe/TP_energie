'''
Constructive heuristics that returns preferably **feasible** solutions.

@author: Vassilissa Lehoux
'''
from typing import Dict, Optional
import random

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.optim.heuristics import Heuristic


class Greedy(Heuristic):
    '''
    A deterministic greedy method to return a solution.
    '''

    def __init__(self, params: Optional[Dict] = None):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
               dictionary. Implementation should provide default values in the function.
        '''
        super().__init__(params)

    def _candidate_score(self, operation, machine):
        """
        Deterministic dispatching score inspired by list scheduling rules.
        Reference: Pinedo, Scheduling (dispatching/list heuristics).
        """
        earliest_start = max(operation.min_start_time, machine.available_time if machine.scheduled_operations else machine.set_up_time)
        processing_time = operation.processing_time_on(machine.machine_id)
        if processing_time < 0:
            return None
        end_time = earliest_start + processing_time
        if end_time > machine.end_time:
            return None

        slack = machine.end_time - end_time
        energy = operation.energy_on(machine.machine_id)
        # Maximize slack first (implemented by minimizing -slack), then energy, then completion time.
        return (-slack, energy, end_time, operation.job_id, operation.operation_id, machine.machine_id)

    def run(self, instance: Instance, params: Optional[Dict] = None) -> Solution:
        '''
        Computes a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).

        @param instance: the instance to solve
        @param params: the parameters for the run
        '''
        _ = {**self.params, **(params or {})}
        solution = Solution(instance)

        while True:
            available_operations = solution.available_operations
            if not available_operations:
                break

            best = None
            for operation in available_operations:
                for machine in instance.machines:
                    if not operation.can_run_on(machine.machine_id):
                        continue
                    score = self._candidate_score(operation, machine)
                    if score is None:
                        continue
                    if best is None or score < best[0]:
                        best = (score, operation, machine)

            if best is None:
                # No feasible local move from this partial schedule.
                break

            _, operation, machine = best
            solution.schedule(operation, machine)

        return solution


class NonDeterminist(Heuristic):
    '''
    Heuristic that returns different values for different runs with the same parameters
    (or different values for different seeds and otherwise same parameters)
    '''

    def __init__(self, params: Optional[Dict] = None):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
               dictionary. Implementation should provide default values in the function.
        '''
        super().__init__(params)

    def run(self, instance: Instance, params: Optional[Dict] = None) -> Solution:
        '''
        Computes a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).

        @param instance: the instance to solve
        @param params: the parameters for the run
        '''
        all_params = {**self.params, **(params or {})}
        seed = all_params.get("seed", None)
        rng = random.Random(seed)

        solution = Solution(instance)

        while True:
            available_operations = solution.available_operations
            if not available_operations:
                break

            candidates = []
            for operation in available_operations:
                for machine in instance.machines:
                    if not operation.can_run_on(machine.machine_id):
                        continue

                    earliest_start = max(
                        operation.min_start_time,
                        machine.available_time if machine.scheduled_operations else machine.set_up_time,
                    )
                    duration = operation.processing_time_on(machine.machine_id)
                    if duration < 0:
                        continue
                    end_time = earliest_start + duration
                    if end_time > machine.end_time:
                        continue
                    candidates.append((operation, machine))

            if not candidates:
                break

            # Uniform random choice among feasible local moves.
            operation, machine = rng.choice(candidates)
            solution.schedule(operation, machine)

        return solution


if __name__ == "__main__":
    # Example of playing with the heuristics
    from src.scheduling.tests.test_utils import TEST_FOLDER_DATA
    import os
    inst = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + "jsp1")
    heur = NonDeterminist()
    sol = heur.run(inst)
    plt = sol.gantt("tab20")
    plt.savefig("gantt.png")
