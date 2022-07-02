import time
from dataclasses import dataclass
from types import SimpleNamespace
from threading import Thread, Lock

from numpy.testing import assert_almost_equal

from instance import *

import gurobipy as gp
from gurobipy import GRB
from abc import ABC, abstractmethod
import numpy as np

delta = 1e-4

@dataclass
class Solution:
    server_order: list
    task_times: dict  # map from task ids to (start, end)
    makespan: float
    solve_time: float = None
    method: str = None
    uuid: UUID = None
    instance: Instance = None

    def __post_init__(self):
        if self.instance is not None:
            self.uuid = self.instance.uuid

    def add_instance(self, instance):
        if self.uuid is not None:
            if instance.uuid != self.uuid:
                raise Exception("Incorrect instance")
        self.instance = instance
        self.uuid = self.instance.uuid

    @staticmethod
    def decode(table, instance : Instance = None):
        return Solution(
            server_order=table['server_order'],
            task_times=table['task_times'],
            makespan=table['makespan'],
            uuid=table['uuid'],
            instance=instance
        )

    def encode(self):
        return {
            'server_order': self.server_order,
            'task_times': self.task_times,
            'makespan': self.makespan,
            'uuid': str(self.uuid)
        }

    def verify(self):
        if self.instance is None:
            raise Exception("Cannot verify without instance")

        # Verify all tasks are scheduled exactly once
        assert len(self.server_order) == len(self.instance.tasks)
        assert len(self.server_order) == len(set(self.server_order) & set(map(lambda t: t.id, self.instance.tasks)))

        # Verify task times match
        for t in self.instance.tasks:
            assert_almost_equal(self.task_times[t.id][1], self.task_times[t.id][0] + t.p + t.s)

        # Verify server ordering
        for i in range(1, len(self.server_order)):
            j1 = self.instance.tasks[self.server_order[i-1]]
            j2 = self.instance.tasks[self.server_order[i]]
            assert self.task_times[j1.id][0] + j1.s <= self.task_times[j2.id][0] + delta

        # Verify machine orderings
        for m in self.instance.machines:
            for i in range(1, len(m.ordering)):
                j1 = m[i - 1]
                j2 = m[i]
                assert self.task_times[j1.id][1] <= self.task_times[j2.id][0] + delta

class Solver(ABC):

    def reset(self):
        self.model = None
        self.relaxed_model = None
        self.instance = None
        self.solution = None
        self.relaxed_solution = None
        self.vars = None
        self.relaxed_vars = None

    def __init__(self, name="model"):
        self.name = name
        self.reset()

    def get_instance(self) -> Instance:
        return self.instance

    def get_model(self, relaxed=False) -> gp.Model:
        if relaxed:
            if self.relaxed_model is None:
                model = self.get_model()
                self.relaxed_model = model.relax()
            return self.relaxed_model
        else:
            if self.model is None:
                raise Exception("Model has not been generated yet")
            return self.model

    def get_solution(self, relaxed) -> Solution:
        if relaxed:
            if self.relaxed_solution is None:
                raise Exception("Relaxed model has not been solved yet")
            return self.relaxed_solution
        else:
            if self.solution is None:
                raise Exception("Model has not been solved yet")
            return self.solution

    def get_variables(self, relax=False):
        if relax:
            if self.relaxed_vars is None:
                self.get_model().update()
                self.relax_vars()
            return self.relaxed_vars
        else:
            if self.vars is None:
                self.vars = SimpleNamespace()
            return self.vars

    def relax_vars(self):
        relaxed_model = self.get_model(True)
        self.relaxed_vars = SimpleNamespace()
        for varname in self.vars.__dict__:
            var = self.vars.__getattribute__(varname)
            if isinstance(var, gp.tupledict):
                var2 = gp.tupledict()
                for item in var:
                    var2[item] = relaxed_model.getVarByName(var[item].VarName)
                self.relaxed_vars.__setattr__(varname, var2)
            elif isinstance(var, gp.Var):
                self.relaxed_vars.__setattr__(varname, relaxed_model.getVarByName(var.VarName))
            elif isinstance(var, np.float) or isinstance(var, np.int64) or isinstance(var, int):
                self.relaxed_vars.__setattr__(varname, var)
            else:
                raise Exception(f"Unknown var type {type(var)}")

    @abstractmethod
    def add_variables(self):
        pass

    @abstractmethod
    def add_constraints(self):
        pass

    @abstractmethod
    def extract_solution(self, relaxed) -> Solution:
        pass

    def solve(self, instance: Instance, standard=True, relaxed=True):
        # Reset entirely
        self.reset()

        self.instance = instance

        self.model = gp.Model(self.name)
        self.model.setParam("TimeLimit", 600)

        self.add_variables()
        self.add_constraints()

        self.get_model().update()

        # Run the optimizer
        if standard:
            self.get_model().optimize()
            if self.get_model().status != GRB.OPTIMAL:
                print(f'Warning: Optimizer exited with status {self.get_model().status}')
                return float('NaN')
            self.solution = self.extract_solution(False)
            self.solution.solve_time = self.get_model().Work
            self.solution.method = None

        if relaxed:
            model = self.get_model(True)

            model.optimize()
            if model.status != GRB.OPTIMAL:
                print(f'Warning: Optimizer exited with status {model.status}')
                return float('NaN')
            self.relaxed_solution = self.extract_solution(True)
            self.relaxed_solution.solve_time = self.get_model(True).Work
            self.relaxed_solution.method = None

    def check_solution(self, assignments, relaxed=False):
        constraints = []
        model = self.get_model(relaxed)
        for var in assignments:
            constraints.append(model.addConstr(var == assignments[var], var.VarName))

        model.optimize()
        status = model.status

        model.remove(constraints)

        return status

