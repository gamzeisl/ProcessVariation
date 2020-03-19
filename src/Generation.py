import sobol_seq
import numpy as np
from src import transistor_count, N, p, o, lower_bound, upper_bound
from src.population import Population


class Generation:
    def __init__(self):
        self.N = N
        self.p = p
        self.transistor_count = transistor_count
        self.o = o
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.individuals = []

    def population_initialize(self):
        for _ in range(self.N):
            qmc = sobol_seq.i4_sobol_generate(1, self.p)
            dif_bound = (np.array(self.upper_bound) - np.array(self.lower_bound))
            variable = list(np.multiply(dif_bound, qmc) + np.array(self.lower_bound))
            self.individuals.append(Population(variable))
