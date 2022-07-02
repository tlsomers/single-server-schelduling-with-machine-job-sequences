from solver import *


class TIVSolver(Solver):
    def __init__(self):
        super().__init__("tivsolver")

    def add_variables(self):
        instance = self.get_instance()
        model = self.get_model()
        variables = self.get_variables()

        variables.T = sum(t.p + t.s for t in instance.tasks)

        variables.C_max = model.addVar(name="C_max", vtype=GRB.CONTINUOUS, lb=0)
        variables.X = model.addVars(len(instance.tasks), int(variables.T), name="X", vtype=GRB.BINARY)

    def add_constraints(self):
        instance = self.get_instance()
        model = self.get_model()
        variables = self.get_variables()

        C_max = variables.C_max
        X = variables.X
        T = variables.T

        # Cmax
        model.addConstrs(
            (gp.quicksum((t + j.s + j.p) * X[j.id, t] for t in range(0, T - j.s - j.p + 1)) <= C_max for j in
             instance.tasks), name="cmax")

        model.addConstrs((gp.quicksum(X[j.id, t] for t in range(0, T - j.s - j.p + 1)) == 1 for j in instance.tasks),
                         name="all_scheduled")
        model.addConstrs((gp.quicksum(X[j.id, t] for t in range(T - j.s - j.p + 1, T)) == 0 for j in instance.tasks),
                         name="all_scheduled_2")

        model.addConstrs((
            gp.quicksum(
                X[j.id, s] for j in instance.tasks for s in range(max(0, t - j.s + 1), t + 1)
            ) <= 1 for t in range(0, T)), name="single_server")

        # Ordering?
        model.addConstrs((
            gp.quicksum(s * X[instance.machines[mi][i].id, s] for s in range(0, T)) + instance.machines[mi][i].s +
            instance.machines[mi][i].p <= gp.quicksum(s * X[instance.machines[mi][i + 1].id, s] for s in range(0, T))
            for mi in range(len(instance.machines)) for i in range(len(instance.machines[mi]) - 1)
        ), name="Ordering")

        model.setObjective(C_max)

    def extract_solution(self, relaxed) -> Solution:
        instance = self.get_instance()
        variables = self.get_variables(relaxed)

        task_times = {}
        starttimes_rev = {}
        for task in instance.tasks:
            sum = 0
            for i in range(variables.T):
                sum = sum + i * variables.X[task.id, i].X
            starttimes_rev[sum] = task.id
            task_times[task.id] = (sum, sum + task.s + task.p)

        order = list(map(lambda i: starttimes_rev[i], sorted(starttimes_rev)))

        return Solution(
            server_order=order,
            task_times=task_times,
            makespan=variables.C_max.X,
            instance=instance
        )
