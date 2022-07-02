from solver import *


class PositionSolver(Solver):
    def __init__(self):
        super().__init__('posmodel')

    def add_variables(self):
        instance = self.get_instance()
        model = self.get_model()
        variables = self.get_variables()

        variables.C_max = model.addVar(name="C_max", vtype=GRB.CONTINUOUS, lb=0)
        variables.C = model.addVars(len(instance.tasks), name="C", vtype=GRB.CONTINUOUS, lb=0)
        variables.Y = model.addVars(len(instance.tasks), len(instance.tasks), name="y", vtype=GRB.BINARY)

    def add_constraints(self):
        instance = self.get_instance()
        model = self.get_model()
        variables = self.get_variables()

        L = sum(t.p + t.s for t in instance.tasks)

        C_max = variables.C_max
        C = variables.C
        Y = variables.Y

        # 22
        model.addConstrs(
            (gp.quicksum(Y[j, i] for j in range(len(instance.tasks))) == 1 for i in range(len(instance.tasks))),
            name="22")

        # 23
        model.addConstrs(
            (gp.quicksum(Y[j, i] for i in range(len(instance.tasks))) == 1 for j in range(len(instance.tasks))),
            name="23")

        # 25
        for machine in instance.machines:
            ordering = machine.ordering
            model.addConstr((C[ordering[0]] >= instance.tasks[ordering[0]].p + instance.tasks[ordering[0]].s),
                            name=f"25a[{machine.id}]")
            model.addConstrs(
                (C[ordering[i]] >= instance.tasks[ordering[i]].p + instance.tasks[ordering[i]].s + C[ordering[i - 1]]
                 for i in range(1, len(ordering))), name=f"25b[{machine.id}]"
            )

        # 26
        model.addConstrs(
            (C[j_1] + L * (2 - Y[j_0, i - 1] - Y[j_1, i]) >=
             C[j_0] - instance.tasks[j_0].p + instance.tasks[j_1].p + instance.tasks[j_1].s
             for j_0 in range(len(instance.tasks))
             for j_1 in range(len(instance.tasks))
             for i in range(1, len(instance.tasks))),
            name="26"
        )

        # 27
        model.addConstrs((C_max >= C[i] for i in range(len(instance.tasks))), name="27")

        # objective
        model.setObjective(C_max)

    def extract_solution(self, relaxed) -> Solution:
        instance = self.get_instance()
        variables = self.get_variables(relaxed)

        if not relaxed:
            order = [0 for i in range(len(instance.tasks))]
            for i in range(len(instance.tasks)):
                for j in range(len(instance.tasks)):
                    if variables.Y[j, i].X > 0.5:
                        order[i] = j

            task_times = {}
            for t in instance.tasks:
                task_times[t.id] = (variables.C[t.id].X - t.p - t.s, variables.C[t.id].X)
        else:
            order = []
            task_times = []

        return Solution(
            server_order=order,
            task_times=task_times,
            makespan=variables.C_max.X,
            instance=instance
        )
