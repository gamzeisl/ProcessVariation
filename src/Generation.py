import sobol_seq
import numpy as np
import pickle
import os
from datetime import datetime

from . import transistor_count, N, p, o, lower_bound, upper_bound
from .population import Population


class Generation:
    def __init__(self):
        self.individuals = []
        self.properties = {
            'N': N, 'p': p, 'o': o, 'transistor_count': transistor_count,
            'lower_bound': lower_bound, 'upper_bound': upper_bound}

    def population_initialize(self):
        for _ in range(self.properties['N']):
            qmc = sobol_seq.i4_sobol_generate(1, self.properties['p'])
            dif_bound = (np.array(self.properties['upper_bound']) -
                         np.array(self.properties['lower_bound']))
            variable = list(np.multiply(dif_bound, qmc) +
                            np.array(self.properties['lower_bound']))
            self.individuals.append(Population(variable))

    def simulate(self):
        """ Simulate each individual inside the generation """
        for ind in self.individuals:
            ind.simulate()


class Generations:
    def __init__(self):
        self.gen = []

    def append(self, generation):
        self.gen.append(generation)

    def plot(self, start, stop):
        pass

    def save(self, start: int,
             stop: int, file_name=None):
        if not file_name:
            today = datetime.now()
            file_name = today.strftime("%Y-%m-%d/%H:%M")
            file_name += 'gen:' + str(start) + ':' + str(stop)
        else:
            if not isinstance(file_name, str):
                raise TypeError(f"File name should be in str type"
                                f"but given {type(file_name)}")
        os.chdir('../data')

        if not isinstance(start, int) or not isinstance(stop, int):
            raise TypeError(f"Stop or start indexes should be"
                            f"integer type")
        if start < stop:
            raise ValueError(f"Stop index can not be higher"
                             f"than start index")
        else:
            with open(file_name, 'w') as f:
                data = self.gen[start:stop+1]
                pickle.dumps(data, f)

