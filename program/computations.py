from sqlalchemy import create_engine, Column, Date, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import myinstances as data

from program.solver import *
from program.positionsolver import PositionSolver
from program.lovsolver import LOVSolver
from program.tivsolver import TIVSolver

engine = create_engine('sqlite:///../db/results.db', echo=True)

Model = declarative_base(name='Model')


class Results(Model):
    __tablename__ = 'results'
    configuration = Column(Integer, primary_key=True)
    instance = Column(Integer, primary_key=True)
    dataset = Column(String, primary_key=True)
    # PIV
    makespan_piv = Column(Float)
    runtime_piv = Column(Float)
    # PIV Relaxation
    makespan_piv_r = Column(Float)
    runtime_piv_r = Column(Float)
    # LOV
    makespan_lov = Column(Float)
    runtime_lov = Column(Float)
    # LOV Relaxation
    makespan_lov_r = Column(Float)
    runtime_lov_r = Column(Float)
    # TIV
    makespan_tiv = Column(Float)
    runtime_tiv = Column(Float)
    method_tiv = Column(String)
    # TIV Relaxation
    makespan_tiv_r = Column(Float)
    runtime_tiv_r = Column(Float)
    method_tiv_r = Column(String)
    # Heuristic Value
    makespan_heuristic = Column(Float)
    runtime_heuristic = Column(Float)
    # Max total machine time
    max_tot_machine_time = Column(Float)


Model.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()

piv_solver = PositionSolver()
lov_solver = LOVSolver()
tiv_solver = TIVSolver()


def single_instance(instance_set: data.InstanceSet, index, i):
    inst = instance_set.instances[i]
    piv_solver.solve(inst)
    lov_solver.solve(inst)
    tiv_solver.solve(inst)
    tot_machine_time = 0
    for machine in inst.machines:
        mach_time = sum(map(lambda i: inst.tasks[i].s + inst.tasks[i].p, machine.ordering))
        if mach_time > tot_machine_time:
            tot_machine_time = mach_time

    res = Results(
        configuration=index,
        instance=i + 1,
        dataset=instance_set.name,
        makespan_piv=piv_solver.get_solution(relaxed=False).makespan,
        runtime_piv=piv_solver.get_solution(relaxed=False).solve_time,
        makespan_piv_r=piv_solver.get_solution(relaxed=True).makespan,
        runtime_piv_r=piv_solver.get_solution(relaxed=True).solve_time,

        makespan_lov=lov_solver.get_solution(relaxed=False).makespan,
        runtime_lov=lov_solver.get_solution(relaxed=False).solve_time,
        makespan_lov_r=lov_solver.get_solution(relaxed=True).makespan,
        runtime_lov_r=lov_solver.get_solution(relaxed=True).solve_time,

        makespan_tiv=tiv_solver.get_solution(relaxed=False).makespan,
        runtime_tiv=tiv_solver.get_solution(relaxed=False).solve_time,
        method_tiv=tiv_solver.get_solution(relaxed=False).method,

        makespan_tiv_r=tiv_solver.get_solution(relaxed=True).makespan,
        runtime_tiv_r=tiv_solver.get_solution(relaxed=True).solve_time,
        method_tiv_r=tiv_solver.get_solution(relaxed=False).method,

        max_tot_machine_time=tot_machine_time
    )
    session.merge(res)
    session.commit()


def runInstanceSets(instances):
    for i in reversed(range(len(instances))):
        instance_set = instances[i]
        for j in range(len(instance_set.instances)):
            print(f"Starting instance {j+1} of configuration {i}.")
            try:
                single_instance(instance_set, i, j)
                print(f"Completed instance {j + 1} of configuration {i}.")
            except Exception:
                print(f"Failed instance {j + 1} of configuration {i}.")
                pass


runInstanceSets(data.instances_I)
