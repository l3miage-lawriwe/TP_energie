'''
Machine on which operation are executed.

@author: Vassilissa Lehoux
'''
from typing import List
from src.scheduling.instance.operation import Operation


class Machine(object):
    '''
    Machine class.
    When operations are scheduled on the machine, contains the relative information. 
    '''

    def __init__(self, machine_id: int, set_up_time: int, set_up_energy: int, tear_down_time: int,
                 tear_down_energy:int, min_consumption: int, end_time: int):
        '''
        Constructor
        Machine is stopped at the beginning of the planning and need to
        be started before executing any operation.
        @param end_time: End of the schedule on this machine: the machine must be
          shut down before that time.
        '''
        self._machine_id = int(machine_id)
        self._set_up_time = int(set_up_time)
        self._set_up_energy = float(set_up_energy)
        self._tear_down_time = int(tear_down_time)
        self._tear_down_energy = float(tear_down_energy)
        self._min_consumption = float(min_consumption)
        self._end_time = int(end_time)
        self._scheduled_operations = []
        self._start_times = []
        self._stop_times = []

    def reset(self):
        self._scheduled_operations = []
        self._start_times = []
        self._stop_times = []

    @property
    def set_up_time(self) -> int:
        return self._set_up_time

    @property
    def tear_down_time(self) -> int:
        return self._tear_down_time

    @property
    def end_time(self) -> int:
        return self._end_time

    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def scheduled_operations(self) -> List:
        '''
        Returns the list of the scheduled operations on the machine.
        '''
        return self._scheduled_operations

    @property
    def available_time(self) -> int:
        """
        Returns the next time at which the machine is available
        after processing its last operation of after its last set up.
        """
        if self._scheduled_operations:
            return self._scheduled_operations[-1].end_time
        if self._start_times:
            return self._start_times[-1] + self._set_up_time
        return 0

    def add_operation(self, operation: Operation, start_time: int) -> int:
        '''
        Adds an operation on the machine, at the end of the schedule,
        as soon as possible after time start_time.
        Returns the actual start time.
        '''
        start_time = int(start_time)
        if not operation.can_run_on(self._machine_id):
            return -1

        if not self._start_times:
            machine_start_time = max(0, start_time - self._set_up_time)
            self._start_times.append(machine_start_time)
            self._stop_times.append(self._end_time)

        actual_start_time = max(start_time, self.available_time)
        if actual_start_time + operation.processing_time_on(self._machine_id) > self._end_time:
            return -1

        if not operation.schedule(self._machine_id, actual_start_time, check_success=True):
            return -1
        self._scheduled_operations.append(operation)
        return actual_start_time

    def stop(self, at_time):
        """
        Stops the machine at time at_time.
        """
        assert(self.available_time >= at_time)
        if not self._start_times:
            return
        self._stop_times[-1] = int(at_time)

    @property
    def working_time(self) -> int:
        '''
        Total time during which the machine is running
        '''
        return sum(stop - start for start, stop in zip(self._start_times, self._stop_times))

    @property
    def start_times(self) -> List[int]:
        """
        Returns the list of the times at which the machine is started
        in increasing order
        """
        return self._start_times

    @property
    def stop_times(self) -> List[int]:
        """
        Returns the list of the times at which the machine is stopped
        in increasing order
        """
        return self._stop_times

    @property
    def total_energy_consumption(self) -> float:
        """
        Total energy consumption of the machine during planning exectution.
        """
        if not self._start_times:
            return 0.0

        setup_teardown = len(self._start_times) * (self._set_up_energy + self._tear_down_energy)
        operation_energy = sum(operation.energy for operation in self._scheduled_operations)
        total_time_on = self.working_time
        total_processing_time = sum(operation.processing_time for operation in self._scheduled_operations)
        idle_time = max(0, total_time_on - total_processing_time - len(self._start_times) * self._set_up_time - len(self._start_times) * self._tear_down_time)
        idle_energy = idle_time * self._min_consumption
        return float(setup_teardown + operation_energy + idle_energy)

    def __str__(self):
        return f"M{self.machine_id}"

    def __repr__(self):
        return str(self)
