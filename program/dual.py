import math

import numpy as np
import tabulate

from program.solver import *
from program.tivsolver import TIVSolver

tiv_solver = TIVSolver()


def rowvector(arr):
    return np.matrix(arr)


def colvector(arr):
    return np.matrix(arr).T


def printmat(mat):
    print(tabulate.tabulate(mat.getA()))


def addMatrixConstraint(model, left, right, comp, name):
    leftarr = left.getA1()
    rightarr = right.getA1()
    if comp == -1:
        model.addConstrs((leftarr[i] <= rightarr[i] for i in range(len(leftarr))), name)
    elif comp == 0:
        model.addConstrs((leftarr[i] == rightarr[i] for i in range(len(leftarr))), name)
    else:
        model.addConstrs((leftarr[i] >= rightarr[i] for i in range(len(leftarr))), name)


def test_dual():
    model_env = gp.Env(empty=True)
    # model_env.setParam('OutputFlag', 0)  # suppress all logging
    model_env.start()
    model = gp.Model("DUAL", env=model_env)

    u_ = model.addVars(2, name="u", vtype=GRB.CONTINUOUS, lb=-math.inf)
    v_ = model.addVars(11, name="v", vtype=GRB.CONTINUOUS, ub=0, lb=-math.inf)
    x_ = model.addVars(5, name="x", vtype=GRB.CONTINUOUS, lb=0)
    model.update()

    u = rowvector(list(map(lambda i: u_[i], u_)))
    v = rowvector(list(map(lambda i: v_[i], v_)))
    x = colvector(list(map(lambda i: x_[i], x_)))

    A = np.matrix("1 1 1 0 0 0 0; " +
                  "0 0 0 1 1 1 0")

    B = np.matrix("1 0 0 0 0 0 0; 0 1 0 0 0 0 0; 0 0 1 0 0 0 0; 0 0 0 1 0 0 0; 0 0 0 0 1 0 0; 0 0 0 0 0 1 0; 1 0 0 1 0 0 0; 0 1 0 0 1 0 0; 0 0 1 0 0 1 0; 0 1 2 0 0 0 -1; 0 0 0 0 1 2 -1")

    a = np.matrix("1; 1")

    b = np.matrix("1; 1; 1; 1; 1; 1; 1; 1; 1; -1; -1")

    c = np.matrix("0 0 0 0 0 0 1")

    # model.setObjective((c * x)[0, 0], GRB.MINIMIZE)
    #
    # addMatrixConstraint(model, A * x, a, -1, "As")
    # addMatrixConstraint(model, B * x, b, 0, "Bs")

    model.setObjective((u * a + v * b)[0, 0], GRB.MAXIMIZE)
    addMatrixConstraint(model, u * A + v * B, c, -1, "xs")

    model.optimize()
    if model.status != GRB.OPTIMAL:
        print(f'Warning: Optimizer exited with status {model.status}')
        return float('NaN')

    print("Optimized")
    printmat(A)
    printmat(B)

    printmat(u)
    printmat(v)
    return model.getObjective().getValue()

print(test_dual())
