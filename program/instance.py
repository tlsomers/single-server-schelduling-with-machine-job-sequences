import re
from dataclasses import dataclass

from uuid import UUID, uuid4
import numpy as np
from pathlib import Path


@dataclass
class Task:
    id: int
    p: float
    s: float

    def __hash__(self):
        return self.id

    @staticmethod
    def decode(table):
        return Task(table['id'], table['p'], table['s'])

    def encode(self):
        return {'id': self.id, 'p': self.p, 's': self.s}


@dataclass
class Machine:
    ordering: list[int]
    instance: object = None
    id: int = 0

    def __getitem__(self, item):
        return self.instance.tasks[self.ordering[item]]

    def __len__(self):
        return len(self.ordering)

    def __str__(self):
        return str(self.id)

    def __hash__(self):
        return self.id

    @staticmethod
    def decode(table):
        return Machine(id=table['id'], ordering=table['ordering'])

    def encode(self):
        return {'id': self.id, 'ordering': self.ordering}


@dataclass
class Instance:
    tasks: list[Task]
    machines: list[Machine]
    uuid: UUID = None

    def __post_init__(self):
        if self.uuid is None:
            self.uuid = uuid4()
        i = 0
        for machine in self.machines:
            machine.instance = self
            machine.id = i
            i += 1

    @staticmethod
    def decode(table):
        return Instance(
            list(map(Task.decode, table['tasks'])),
            list(map(Machine.decode, table['machines'])),
            UUID(table['uuid'])
        )

    def encode(self):
        return {
            'uuid': str(self.uuid),
            'tasks': list(map(lambda t: t.encode(), self.tasks)),
            'machines': list(map(lambda m: m.encode(), self.machines))
        }

    # Generate a random instance of the machine sequence problem with s=1 and p ~ [0, 20].
    @staticmethod
    def generate(setups, processing, machineCounts):
        task_count = sum(machineCounts)
        tasks = []
        for i in range(task_count):
            s, p = None, None
            if type(setups) == int:
                s = setups
            else:
                s = setups()
            if type(processing) == int:
                p = processing
            else:
                p = processing()
            tasks.append(Task(id=i, p=p, s=s))
        ids = list(range(task_count))
        machines = []
        for m in range(len(machineCounts)):
            machines.append(Machine(ordering=ids[0:machineCounts[m]]))
            ids = ids[machineCounts[m]:]
        return Instance(tasks=tasks, machines=machines)

    @staticmethod
    def from_file(path):
        if isinstance(path, str):
            path = Path(path)
        with open(path) as f:
            # Skip over description
            f.readline()
            while f.readline().strip() != "---------------":
                pass

            # Actual data
            [n, m] = list(map(int, f.readline().split()))
            machineCounts = list(map(int, f.readline().split()))
            tasks = []
            machines = []
            for i in range(n):
                [s, p] = list(map(int, f.readline().split()))
                tasks.append(Task(id=i, s=s, p=p))
            id = 0
            for i in range(len(machineCounts)):
                machines.append(Machine(id=i, ordering=list(range(id, id + machineCounts[i]))))
                id = id + machineCounts[i]
            return Instance(tasks=tasks, machines=machines)

    def reorder(self):
        mapping = {}
        i = 0
        for machinei in range(len(self.machines)):
            machine = self.machines[machinei]
            machine.id = machinei
            for j in range(len(machine.ordering)):
                mapping[machine.ordering[j]] = i
                machine.ordering[j] = i
                i = i + 1

        for task in self.tasks:
            task.id = mapping[task.id]

        self.tasks.sort(key=lambda t: t.id)
        self.machines.sort(key=lambda t: t.id)

    def to_file(self, path, comments=""):
        if isinstance(path, str):
            path = Path(path)
        self.reorder()
        f = open(path, "w")
        f.write("---------------\n")
        f.write(comments)
        f.write("\n---------------\n")
        f.write(f"{len(self.tasks)} {len(self.machines)}\n")
        f.write(" ".join(map(lambda m: str(len(m.ordering)), self.machines)) + "\n")
        for task in self.tasks:
            f.write(f"{task.s} {task.p}\n")
        f.close()
