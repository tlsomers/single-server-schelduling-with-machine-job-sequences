from solver import *


class LOVSolver(Solver):
    def __init__(self):
        super().__init__("lovsolver")

    def add_variables(self):
        instance = self.get_instance()
        model = self.get_model()
        variables = self.get_variables()

        variables.C_max = model.addVar(name="C_max", vtype=GRB.CONTINUOUS, lb=0)
        variables.C = model.addVars(len(instance.tasks), name="C", vtype=GRB.CONTINUOUS, lb=0)
        variables.Delta = model.addVars(len(instance.tasks), len(instance.tasks), name="delta", vtype=GRB.BINARY)
        variables.L = sum(t.p + t.s for t in instance.tasks)

    def add_constraints(self):
        instance = self.get_instance()
        model = self.get_model()
        variables = self.get_variables()

        C_max = variables.C_max
        C = variables.C
        Delta = variables.Delta
        L = variables.L

        model.addConstrs(
            (Delta[i, i] == 0 for i in range(len(instance.tasks))),
            name="Delta0")

        model.addConstrs(
            (Delta[i, j] + Delta[j, i] == 1 for i in range(len(instance.tasks)) for j in range(i)),
            name="Delta1")

        model.addConstrs(
            (Delta[i, k] >= Delta[i, j] + Delta[j, k] - 1
             for i in range(len(instance.tasks))
             for j in range(len(instance.tasks))
             for k in range(len(instance.tasks))),
            name="Delta2")

        for machine in instance.machines:
            ordering = machine.ordering
            model.addConstrs(
                (Delta[ordering[i], ordering[j]] == 1 for j in range(len(ordering)) for i in range(j)),
                name=f"Initial[{machine.id}]")
            model.addConstr((C[ordering[0]] >= instance.tasks[ordering[0]].p + instance.tasks[ordering[0]].s),
                            name=f"25a[{machine.id}]")
            model.addConstrs(
                (C[ordering[i]] >= instance.tasks[ordering[i]].p + instance.tasks[ordering[i]].s + C[ordering[i - 1]]
                 for i in range(1, len(ordering))), name=f"25b[{machine.id}]"
            )

        # 26
        model.addConstrs(
            (C[j_1] + L * (1 - Delta[j_0, j_1]) >=
             C[j_0] - instance.tasks[j_0].p + instance.tasks[j_1].p + instance.tasks[j_1].s
             for j_0 in range(len(instance.tasks))
             for j_1 in range(len(instance.tasks))),
            name="26"
        )

        # 27
        model.addConstrs((C_max >= C[i] for i in range(len(instance.tasks))), name="27")

        model.setObjective(C_max)

    def extract_solution(self, relaxed) -> Solution:
        instance = self.get_instance()
        variables = self.get_variables(relaxed)

        order = {}
        for i in range(len(instance.tasks)):
            ind = 0
            for j in range(len(instance.tasks)):
                ind += variables.Delta[j, i].X
            order[ind] = i

        order2 = list(map(lambda i: order[i], order))

        task_times = {}
        for t in instance.tasks:
            task_times[t.id] = (variables.C[t.id].X - t.p - t.s, variables.C[t.id].X)

        return Solution(
            server_order=order2,
            task_times=task_times,
            makespan=variables.C_max.X,
            instance=instance
        )
