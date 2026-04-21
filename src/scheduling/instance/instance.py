'''
Information for the instance of the optimization problem.

'''
from typing import List
import os
import csv

from src.scheduling.instance.job import Job
from src.scheduling.instance.operation import Operation
from src.scheduling.instance.machine import Machine


class Instance(object):
    '''
    classdocs
    '''

    def __init__(self, instance_name):
        '''
        Constructor
        '''
        self._instance_name = instance_name
        self._jobs = []
        self._operations = []
        self._machines = []
        self._jobs_by_id = {}
        self._operations_by_id = {}
        self._machines_by_id = {}

    @classmethod
    def from_file(cls, folderpath):
        inst = cls(os.path.basename(folderpath))
        # Reading the operation info
        with open(folderpath + os.path.sep + inst._instance_name + '_op.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for row in csv_reader:
                job_id = int(row[0])
                operation_id = int(row[1])
                machine_id = int(row[2])
                processing_time = int(row[3])
                energy_consumption = int(row[4])

                if job_id not in inst._jobs_by_id:
                    job = Job(job_id)
                    inst._jobs_by_id[job_id] = job
                    inst._jobs.append(job)
                job = inst._jobs_by_id[job_id]

                if operation_id not in inst._operations_by_id:
                    operation = Operation(job_id, operation_id)
                    inst._operations_by_id[operation_id] = operation
                    inst._operations.append(operation)
                    job.add_operation(operation)
                operation = inst._operations_by_id[operation_id]
                operation.add_machine_option(machine_id, processing_time, energy_consumption)

        # reading machine info
        with open(folderpath + os.path.sep + inst._instance_name + '_mach.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for row in csv_reader:
                machine = Machine(
                    machine_id=int(row[0]),
                    set_up_time=int(row[1]),
                    set_up_energy=int(row[2]),
                    tear_down_time=int(row[3]),
                    tear_down_energy=int(row[4]),
                    min_consumption=int(row[5]),
                    end_time=int(row[6]),
                )
                inst._machines.append(machine)
                inst._machines_by_id[machine.machine_id] = machine

        inst._jobs.sort(key=lambda job: job.job_id)
        inst._operations.sort(key=lambda operation: operation.operation_id)
        inst._machines.sort(key=lambda machine: machine.machine_id)
        return inst

    @property
    def name(self):
        return self._instance_name

    @property
    def machines(self) -> List[Machine]:
        return self._machines

    @property
    def jobs(self) -> List[Job]:
        return self._jobs

    @property
    def operations(self) -> List[Operation]:
        return self._operations

    @property
    def nb_jobs(self):
        return len(self._jobs)

    @property
    def nb_machines(self):
        return len(self._machines)

    @property
    def nb_operations(self):
        return len(self._operations)

    def __str__(self):
        return f"{self.name}_M{self.nb_machines}_J{self.nb_jobs}_O{self.nb_operations}"

    def get_machine(self, machine_id) -> Machine:
        return self._machines_by_id.get(machine_id)

    def get_job(self, job_id) -> Job:
        return self._jobs_by_id.get(job_id)

    def get_operation(self, operation_id) -> Operation:
        return self._operations_by_id.get(operation_id)
