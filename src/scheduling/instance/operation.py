'''
Operation of a job.
Its duration and energy consumption depends on the machine on which it is executed.
When operation is scheduled, its schedule information is updated.

@author: Vassilissa Lehoux
'''
from typing import List


class OperationScheduleInfo(object):
    '''
    Informations known when the operation is scheduled
    '''

    def __init__(self, machine_id: int, schedule_time: int, duration: int, energy_consumption: int):
        self.machine_id = machine_id
        self.schedule_time = schedule_time
        self.duration = duration
        self.energy_consumption = energy_consumption


class Operation(object):
    '''
    Operation of the jobs
    '''

    def __init__(self, job_id, operation_id):
        '''
        Constructor
        '''
        self._job_id = int(job_id)
        self._operation_id = int(operation_id)
        self._predecessors = []
        self._successors = []
        self._machine_processing_times = {}
        self._machine_energy = {}
        self._schedule_info = None

    def __str__(self):
        '''
        Returns a string representing the operation.
        '''
        base_str = f"O{self.operation_id}_J{self.job_id}"
        if self._schedule_info:
            return base_str + f"_M{self.assigned_to}_ci{self.processing_time}_e{self.energy}"
        else:
            return base_str

    def __repr__(self):
        return str(self)

    def reset(self):
        '''
        Removes scheduling informations
        '''
        self._schedule_info = None

    def add_predecessor(self, operation):
        '''
        Adds a predecessor to the operation
        '''
        if operation not in self._predecessors:
            self._predecessors.append(operation)

    def add_successor(self, operation):
        '''
        Adds a successor operation
        '''
        if operation not in self._successors:
            self._successors.append(operation)

    def add_machine_option(self, machine_id: int, processing_time: int, energy_consumption: int):
        """
        Adds a feasible machine for this operation.
        """
        self._machine_processing_times[int(machine_id)] = int(processing_time)
        self._machine_energy[int(machine_id)] = int(energy_consumption)

    def can_run_on(self, machine_id: int) -> bool:
        return int(machine_id) in self._machine_processing_times

    def processing_time_on(self, machine_id: int) -> int:
        return self._machine_processing_times.get(int(machine_id), -1)

    def energy_on(self, machine_id: int) -> int:
        return self._machine_energy.get(int(machine_id), -1)

    @property
    def operation_id(self) -> int:
        return self._operation_id

    @property
    def job_id(self) -> int:
        return self._job_id

    @property
    def predecessors(self) -> List:
        """
        Returns a list of the predecessor operations
        """
        return self._predecessors

    @property
    def successors(self) -> List:
        '''
        Returns a list of the successor operations
        '''
        return self._successors

    @property
    def assigned(self) -> bool:
        '''
        Returns True if the operation is assigned
        and False otherwise
        '''
        return self._schedule_info is not None

    @property
    def assigned_to(self) -> int:
        '''
        Returns the machine ID it is assigned to if any
        and -1 otherwise
        '''
        return self._schedule_info.machine_id if self.assigned else -1

    @property
    def processing_time(self) -> int:
        '''
        Returns the processing time if is assigned,
        -1 otherwise
        '''
        return self._schedule_info.duration if self.assigned else -1

    @property
    def start_time(self) -> int:
        '''
        Returns the start time if is assigned,
        -1 otherwise
        '''
        return self._schedule_info.schedule_time if self.assigned else -1

    @property
    def end_time(self) -> int:
        '''
        Returns the end time if is assigned,
        -1 otherwise
        '''
        return self.start_time + self.processing_time if self.assigned else -1

    @property
    def energy(self) -> int:
        '''
        Returns the energy consumption if is assigned,
        -1 otherwise
        '''
        return self._schedule_info.energy_consumption if self.assigned else -1

    def is_ready(self, at_time) -> bool:
        '''
        Returns True if all the predecessors are assigned
        and processed before at_time.
        False otherwise
        '''
        for predecessor in self.predecessors:
            if not predecessor.assigned or predecessor.end_time > at_time:
                return False
        return True

    def schedule(self, machine_id: int, at_time: int, check_success=True) -> bool:
        '''
        Schedules an operation. Updates the schedule information of the operation
        @param check_success: if True, check if all the preceeding operations have
          been scheduled and if the schedule time is compatible
        '''
        if self.assigned:
            return False
        machine_id = int(machine_id)
        at_time = int(at_time)
        if machine_id not in self._machine_processing_times:
            return False
        if check_success and not self.is_ready(at_time):
            return False
        self._schedule_info = OperationScheduleInfo(
            machine_id=machine_id,
            schedule_time=at_time,
            duration=self._machine_processing_times[machine_id],
            energy_consumption=self._machine_energy[machine_id],
        )
        return True

    @property
    def min_start_time(self) -> int:
        '''
        Minimum start time given the precedence constraints
        '''
        if not self.predecessors:
            return 0
        if not all(predecessor.assigned for predecessor in self.predecessors):
            return -1
        return max(predecessor.end_time for predecessor in self.predecessors)

    def schedule_at_min_time(self, machine_id: int, min_time: int) -> bool:
        '''
        Try and schedule the operation af or after min_time.
        Return False if not possible
        '''
        op_min_start = self.min_start_time
        if op_min_start < 0:
            return False
        start_time = max(int(min_time), op_min_start)
        return self.schedule(machine_id, start_time, check_success=True)
