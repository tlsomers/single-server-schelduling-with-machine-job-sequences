from instance import *


def U(low, high):
    def inner():
        return np.random.randint(low, high+1)
    inner.name = f"U[{low}, {high}]"
    return inner


def describe(s, p, machines, i):
    return f"""Jobs: {sum(machines)}, Machines: {len(machines)}
Setup time: {s if type(s) == int else s.name}
Processing time: {p if type(p) == int else p.name}
Jobs per machine: {" ".join(map(lambda mi: f"n_{mi+1}={machines[mi]}", range(len(machines))))}
Instance: {i+1}"""

configuration_IIA = [
    (1, U(0, i), [10, 10, 10]) for i in range(1, 20)
]

configuration_IIB = [
    (U(1, 3), U(0, i), [10, 10, 10]) for i in range(1, 20)
]

configuration_IIIA = [
    (1, U(0, i), [6, 6, 6, 6, 6]) for i in range(1, 20)
]

configuration_IIIB = [
    (U(1, 3), U(0, i), [6, 6, 6, 6, 6]) for i in range(1, 20)
]


def create_instances(config, file, n=10):
    instances = []
    for i in range(n):
        inst = Instance.generate(*config)
        instances.append(inst)
        inst.to_file(file + f"_{i+1}.txt", describe(*config, i))
        instances.append(inst)
    return instances


configurations_I = [
    (30, 3, 1),
    (30, 3, 2),
    (50, 3, 1),
    (50, 3, 2),
    (100, 3, 1),
    (100, 3, 2),
    (30, 5, 1),
    (30, 5, 2),
    (50, 5, 1),
    (50, 5, 2),
    (100, 5, 1),
    (100, 5, 2)
]

@dataclass
class InstanceSet:
    name: str
    config: tuple
    instances: list


def read_config_instances(name, configs, file, n=10):
    lst = []
    for i in range(len(configs)):
        instances = []
        for j in range(n):
            instances.append(Instance.from_file(file + f"_{i+1}_{j+1}.txt"))
        lst.append(InstanceSet(name=name, config=configs[i], instances=instances))
    return lst


instances_I = read_config_instances("I", configurations_I, "../dataset1/data")
instances_IIA = read_config_instances("IIA", configuration_IIA, "../dataset2a/data")
instances_IIB = read_config_instances("IIB", configuration_IIB, "../dataset2b/data")
instances_IIIA = read_config_instances("IIIA", configuration_IIIA, "../dataset3a/data")
instances_IIIB = read_config_instances("IIIB", configuration_IIIB, "../dataset3b/data")

