'''
Object containing the solution to the optimization problem.

@author: Vassilissa Lehoux
'''
from typing import List
import csv
import os
from src.scheduling.instance.instance import Instance
from src.scheduling.instance.operation import Operation
from src.scheduling.instance.machine import Machine


class _FallbackPlot(object):
    """
    Minimal replacement used in tests when matplotlib is unavailable.
    """

    def savefig(self, filepath):
        with open(filepath, "wb") as file_handle:
            file_handle.write(b"")


class Solution(object):
    '''
    Solution class
    '''

    def __init__(self, instance: Instance):
        '''
        Constructor
        '''
        self._instance = instance
        self.reset()


    @property
    def inst(self):
        '''
        Returns the associated instance
        '''
        return self._instance


    def reset(self):
        '''
        Resets the solution: everything needs to be replanned
        '''
        for machine in self._instance.machines:
            machine.reset()
        for job in self._instance.jobs:
            job.reset()

    @property
    def is_feasible(self) -> bool:
        '''
        Returns True if the solution respects the constraints.
        To call this function, all the operations must be planned.
        '''
        if any(not operation.assigned for operation in self.all_operations):
            return False

        for operation in self.all_operations:
            for predecessor in operation.predecessors:
                if predecessor.end_time > operation.start_time:
                    return False

        for machine in self._instance.machines:
            if machine.stop_times and machine.stop_times[-1] > machine.end_time:
                return False
            machine_operations = sorted(machine.scheduled_operations, key=lambda operation: operation.start_time)
            for op1, op2 in zip(machine_operations, machine_operations[1:]):
                if op2.start_time < op1.end_time:
                    return False
                if op1.end_time > machine.end_time:
                    return False
            if machine_operations and machine_operations[-1].end_time > machine.end_time:
                return False
        return True

    @property
    def evaluate(self) -> float:
        '''
        Computes the value of the solution
        '''
        if self.is_feasible:
            return self.objective
        # High penalty for infeasible solutions.
        return 1_000_000_000.0 + self.total_energy_consumption + self.cmax + self.sum_ci

    @property
    def objective(self) -> float:
        '''
        Returns the value of the objective function
        '''
        return float(self.total_energy_consumption + self.cmax + self.sum_ci)

    @property
    def cmax(self) -> int:
        '''
        Returns the maximum completion time of a job
        '''
        completion_times = [job.completion_time for job in self._instance.jobs if job.completion_time >= 0]
        return max(completion_times) if completion_times else -1

    @property
    def sum_ci(self) -> int:
        '''
        Returns the sum of completion times of all the jobs
        '''
        completion_times = [job.completion_time for job in self._instance.jobs]
        if any(ci < 0 for ci in completion_times):
            return -1
        return sum(completion_times)

    @property
    def total_energy_consumption(self) -> float:
        '''
        Returns the total energy consumption for processing
        all the jobs (including energy for machine switched on but doing nothing).
        '''
        return sum(machine.total_energy_consumption for machine in self._instance.machines)

    def __str__(self) -> str:
        '''
        String representation of the solution
        '''
        return f"Solution({self._instance.name}, feasible={self.is_feasible}, objective={self.evaluate})"

    def to_csv(self):
        '''
        Save the solution to a csv files with the following formats:
        Operation file:
          One line per operation
          operation id - machine to which it is assigned - start time
          header: "operation_id,machine_id,start_time"
        Machine file:
          One line per pair of (start time, stop time) for the machine
          header: "machine_id, start_time, stop_time"
        '''
        op_file = self._instance.name + "_sol_operations.csv"
        mach_file = self._instance.name + "_sol_machines.csv"

        with open(op_file, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["operation_id", "machine_id", "start_time"])
            for operation in self.all_operations:
                if operation.assigned:
                    writer.writerow([operation.operation_id, operation.assigned_to, operation.start_time])

        with open(mach_file, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["machine_id", "start_time", "stop_time"])
            for machine in self._instance.machines:
                for start_time, stop_time in zip(machine.start_times, machine.stop_times):
                    writer.writerow([machine.machine_id, start_time, stop_time])

    def from_csv(self, inst_folder, operation_file, machine_file):
        '''
        Reads a solution from the instance folder
        '''
        _ = machine_file
        self.reset()
        with open(os.path.join(inst_folder, operation_file), 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)

        # Reading from CSV assumes rows are already sorted by start time for each machine.
        rows.sort(key=lambda row: int(row["start_time"]))
        for row in rows:
            operation = self._instance.get_operation(int(row["operation_id"]))
            machine = self._instance.get_machine(int(row["machine_id"]))
            self.schedule(operation, machine)

    @property
    def available_operations(self)-> List[Operation]:
        '''
        Returns the available operations for scheduling:
        all constraints have been met for those operations to start
        '''
        available = []
        for job in self._instance.jobs:
            operation = job.next_operation
            if operation is not None:
                available.append(operation)
        return available

    @property
    def all_operations(self) -> List[Operation]:
        '''
        Returns all the operations in the instance
        '''
        return self._instance.operations

    def schedule(self, operation: Operation, machine: Machine):
        '''
        Schedules the operation at the end of the planning of the machine.
        Starts the machine if stopped.
        @param operation: an operation that is available for scheduling
        '''
        assert(operation in self.available_operations)
        if not operation.can_run_on(machine.machine_id):
            raise ValueError(f"Operation {operation.operation_id} cannot be scheduled on machine {machine.machine_id}")

        min_start = operation.min_start_time
        if min_start < 0:
            raise ValueError("Operation predecessors are not all scheduled")

        start_time = machine.add_operation(operation, min_start)
        if start_time < 0:
            raise ValueError(f"Cannot schedule operation {operation.operation_id} on machine {machine.machine_id}")

        self._instance.get_job(operation.job_id).schedule_operation()

    def gantt(self, colormapname):
        """
        Generate a plot of the planning.
        Standard colormaps can be found at https://matplotlib.org/stable/users/explain/colors/colormaps.html
        """
        try:
            from matplotlib import pyplot as plt
            from matplotlib import colormaps
        except ModuleNotFoundError:
            return _FallbackPlot()

        fig, ax = plt.subplots()
        colormap = colormaps[colormapname]
        for machine in self.inst.machines:
            machine_operations = sorted(machine.scheduled_operations, key=lambda op: op.start_time)
            for operation in machine_operations:
                operation_start = operation.start_time
                operation_end = operation.end_time
                operation_duration = operation_end - operation_start
                operation_label = f"O{operation.operation_id}_J{operation.job_id}"
    
                # Set color based on job ID
                color_index = operation.job_id + 2
                if color_index >= colormap.N:
                    color_index = color_index % colormap.N
                color = colormap(color_index)
    
                ax.broken_barh(
                    [(operation_start, operation_duration)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=color,
                    edgecolor='black'
                )

                middle_of_operation = operation_start + operation_duration / 2
                ax.text(
                    middle_of_operation,
                    machine.machine_id,
                    operation_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )
            set_up_time = machine.set_up_time
            tear_down_time = machine.tear_down_time
            for (start, stop) in zip(machine.start_times, machine.stop_times):
                start_label = "set up"
                stop_label = "tear down"
                ax.broken_barh(
                    [(start, set_up_time)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=colormap(0),
                    edgecolor='black'
                )
                ax.broken_barh(
                    [(stop, tear_down_time)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=colormap(1),
                    edgecolor='black'
                )
                ax.text(
                    start + set_up_time / 2.0,
                    machine.machine_id,
                    start_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )
                ax.text(
                    stop + tear_down_time / 2.0,
                    machine.machine_id,
                    stop_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )          

        fig = ax.figure
        fig.set_size_inches(12, 6)
    
        ax.set_yticks(range(self._instance.nb_machines))
        ax.set_yticklabels([f'M{machine_id+1}' for machine_id in range(self.inst.nb_machines)])
        ax.set_xlabel('Time')
        ax.set_ylabel('Machine')
        ax.set_title('Gantt Chart')
        ax.grid(True)
    
        return plt
