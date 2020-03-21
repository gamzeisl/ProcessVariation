import sobol_seq
import numpy as np
import pickle
import os
import math
from matplotlib import pyplot as plt
from datetime import datetime

from . import transistor_count, N, p, o, d, \
    lower_bound, upper_bound, min_pm, max_area, max_power
from .population import Population


class Generation:
    def __init__(self, N):
        self.individuals = []
        self.properties = {
            'N': N, 'p': p, 'o': o, 'transistor_count': transistor_count,
            'lower_bound': lower_bound, 'upper_bound': upper_bound}
        self.archive = []
        self.sat_individuals = []

    def population_initialize(self):
        qmc = sobol_seq.i4_sobol_generate(self.properties['p'],
                                          self.properties['N'])
        dif_bound = (np.array(self.properties['upper_bound']) -
                     np.array(self.properties['lower_bound']))

        variable = np.multiply(qmc, dif_bound) + \
                   np.array(self.properties['lower_bound'])
        for var in variable:
            self.individuals.append(Population(var.tolist()))

    def simulate(self):
        """ Simulate each individual inside the generation """
        for ind in self.individuals:
            ind.simulate()
            if ind.saturation:
                self.sat_individuals.append(ind)

    def plot_scatter(self, gaintype=None, color='b'):
        """ Plot the generation """
        if gaintype == 'db':
            gain = [ind.gaindb for ind in self.individuals]
        elif gaintype == 'mag':
            gain = [ind.gainmag for ind in self.individuals]
        else:
            raise ValueError(f"gaintype should be db or mag")

        bw = [ind.bw for ind in self.individuals]

        plt.scatter(bw, gain, color=color)

    def fitness1(self):
        bw_normalize = 10e+3
        gain_normalize = 1

        pm_error, power_error, \
        area_error = [[0] * N] * 3

        for i, ind in enumerate(self.individuals):
            ind.f_values = {'total_error': 0, 'strength': 0,
                            'rawfitness': 0, 'distance': [0] * N,
                            'fitness': 0}

            if ind.pm < min_pm:
                pm_error[i] = abs(min_pm - ind.pm) / min_pm

            if ind.power > max_power:
                power_error[i] = abs(max_power - ind.power) / max_power

            if ind.area > max_area:
                area_error[i] = abs(max_area - ind.area) / max_area

            ind.f_values['total_error'] = \
                pm_error[i] + power_error[i] + area_error[i]

        # assign strength, distance and rawfitness to each individuals
        for ind1 in self.individuals:

            for j, ind2 in enumerate(self.individuals):
                if ind1.bw > ind2.bw and ind1.gaindb > ind2.gaindb:
                    ind1.f_values['strength'] += 1
                elif ind1.bw < ind2.bw and ind1.gaindb < ind2.gaindb:
                    ind1.f_values['rawfitness'] += 1

                ind1.f_values.get('distance')[j] = math.sqrt(
                    ((ind1.bw - ind2.bw) / bw_normalize) ** 2 +
                    ((ind1.gaindb - ind2.gaindb) / gain_normalize) ** 2)

            ind1.f_values['distance'].sort()

        rawfitnesses = [ind.f_values['rawfitness']
                        for ind in self.individuals]

        for i, ind in enumerate(self.individuals):
            ind.f_values['fitness'] = \
                ind.f_values['rawfitness'] / max(rawfitnesses) + \
                ind.f_values['total_error'] * 20 + 1 / (ind.f_values.get('distance')[d] + 2)

    def enviromental1(self):

        for ind in self.individuals:
            if (ind.f_values['rawfitness'] == 0 and
                    ind.f_values['total_error'] == 0):
                self.archive.append(ind)

        sorted_inds = sorted(self.individuals,
                             key=lambda x: x.f_values['fitness'])

        while len(self.archive) < N:
            for ind in sorted_inds:
                if ind.f_values['rawfitness'] > 0 and \
                        ind.f_values['total_error']:
                    self.archive.append(ind)


class Generations:
    def __init__(self):
        self.gens = []
        self.saturation_inds = []
        self.all_inds = []

    def append(self, generation):
        self.gens.append(generation)
        for ind in generation.individuals:
            self.all_inds.append(ind)
            if ind.saturation:
                self.saturation_inds.append(ind)

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
                data = self.gens[start:stop + 1]
                pickle.dumps(data, f)

    # def new_generation(self):
    #     bw = [ind.bw for ind in self.gens[-1].individuals]
    #     gain = [ind.gain for ind in self.gens[-1].individuals]
    #     pm = [ind.pm for ind in self.gens[-1].individuals]
    #     area = [ind.area for ind in self.gens[-1].individuals]
    #     power = [ind.power for ind in self.gens[-1].individuals]
    #
    # def fitness2(self):
