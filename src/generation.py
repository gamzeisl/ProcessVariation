import sobol_seq
import numpy as np
import pickle
import os
import math
import time

from matplotlib import pyplot as plt
from datetime import datetime
from random import randrange, uniform

from . import transistor_count, N, p, o, d, \
    lower_bound, upper_bound, min_pm, max_area, max_power
from .population import Population


class Generation:
    def __init__(self, N: int):
        self.individuals = []
        self.properties = {
            'N': N, 'p': p, 'o': o, 'transistor_count': transistor_count,
            'max_area': max_area, 'max_power': max_power, 'min_pm': min_pm,
            'lower_bound': lower_bound, 'upper_bound': upper_bound}
        self.archive_inds = []
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

    @classmethod
    def new_generation(cls, parameters: 'list of lists', n: int):

        gen = Generation(n)
        for params in parameters:
            ind = Population(params)
            gen.individuals.append(ind)

        return gen

    def simulate(self):
        """ Simulate each individual inside the generation """
        for ind in self.individuals:
            ind.simulate()
            if ind.saturation:
                self.sat_individuals.append(ind)

    def plot_scatter(self, gaintype: str = None, color='b'):
        """ Plot the generation """
        if gaintype == 'db':
            gain = [ind.gaindb for ind in self.individuals]
        elif gaintype == 'mag':
            gain = [ind.gainmag for ind in self.individuals]
        else:
            raise ValueError(f"gaintype should be db or mag")

        bw = [ind.bw for ind in self.individuals]

        plt.scatter(bw, gain, color=color)
        time.sleep(1)

    def fitness1(self):
        """ Assign fitness values to the first generation"""
        bw_normalize = 10e+3
        gain_normalize = 1
        self.calculate_error()
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

    def fitness2(self, before_generation, kii):
        """ Assign fitness values to the generation except the first."""
        bw_normalize = 10e+3
        gain_normalize = 1
        self.calculate_error()

        archive_pm_error = [0] * N
        archive_power_error = [0] * N
        archive_area_error = [0] * N
        for i, arch_ind_before in enumerate(
                before_generation.archive_inds):

            if arch_ind_before.pm < min_pm:
                archive_pm_error[i] = abs(min_pm - arch_ind_before.pm) / min_pm
            if arch_ind_before.power > max_power:
                archive_power_error[i] = abs(arch_ind_before.power - max_power) / max_power
            if arch_ind_before.area > max_area:
                archive_area_error[i] = abs(arch_ind_before.area - max_area) / max_area

            self.individuals[i].f_archive_values['total_error'] = \
                archive_pm_error[i] + archive_power_error[i] + archive_area_error[i]

        # Assign strength values to new generation
        for ind1 in self.individuals:
            for j, ind2 in enumerate(self.individuals):

                if ind1.bw > ind2.bw and ind1.gaindb > ind2.gaindb:
                    ind1.f_values['strength'] += 1

                if ind1.bw > before_generation.archive_inds[j].bw and \
                        ind1.gain > before_generation.archive_inds[j].gaindb:
                    ind1.f_values['strength'] += 1

        # Assign strength values to archive
        for i, arch_ind_before in enumerate(before_generation.archive_inds):
            for j, ind in enumerate(self.individuals):

                if arch_ind_before.bw > ind.bw and arch_ind_before.gaindb > ind.gaindb:
                    self.individuals[i].f_archive_values['strength'] += 1

                if arch_ind_before.bw > before_generation.archive_inds[j].bw and \
                        arch_ind_before.gaindb > before_generation.archive_inds[j].gaindb:
                    self.individuals[i].f_archive_values['strength'] += 1

        # Assign rawfitness values to new generation
        for ind1 in self.individuals:
            for j, ind2 in enumerate(self.individuals):

                if ind1.bw < ind2.bw and ind1.gaindb < ind2.gaindb:
                    ind1.f_values['rawfitness'] += ind2.f_values['strength']

                if ind1.bw < before_generation.archive_inds[j].bw and \
                        ind1.gaindb < before_generation.archive_inds[j].gaindb:
                    ind1.f_values['rawfitness'] += \
                        ind2.f_archive_values['strength']

        # Assign rawfitness values to archive
        for i, arch_ind_before in enumerate(before_generation.archive_inds):
            for j, ind in enumerate(self.individuals):

                if arch_ind_before.bw < ind.bw and arch_ind_before.gaindb < ind.gaindb:
                    self.individuals[i].f_archive_values['rawfitness'] += \
                        ind.f_values['strength']

                if arch_ind_before.bw < before_generation.archive_inds[j].bw and \
                        arch_ind_before.gaindb < before_generation.archive_inds[j].gaindb:
                    self.individuals[i].f_archive_values['rawfitness'] += \
                        ind.f_archive_values['strength']

        for ind in self.individuals:

            # Calculate distance values
            for j, arch_ind_before in enumerate(before_generation.archive_inds):
                ind.f_values.get('distance')[j] = math.sqrt(
                    ((ind.bw - arch_ind_before.bw) / bw_normalize) ** 2 +
                    ((ind.gaindb - arch_ind_before.gaindb) / gain_normalize) ** 2)
                ind.f_archive_values['distance'][j] = math.sqrt(
                    ((arch_ind_before.bw - before_generation.archive_inds[j].bw) / bw_normalize) ** 2 +
                    ((arch_ind_before.gaindb - before_generation.archive_inds[j].gaindb) / gain_normalize) ** 2)

            all_rawfitness = [ind.f_values['rawfitness']
                              for ind in self.individuals]

            all_archive_rawfitness = [ind.f_archive_values['rawfitness']
                                      for ind in self.individuals]

            ind.f_values['distance'].sort()

            # normalize rawfitness and add error to generation
            if max(all_rawfitness) != 0:
                ind.f_values['fitness'] = ind.f_values['rawfitness'] / max(all_rawfitness) \
                                          + ind.f_values['total_error'] * (20 + (kii ** 4) * 1e-8) \
                                          + 0.1 / (ind.f_values['distance'][d] + 2)
            else:
                ind.f_values['fitness'] = ind.f_values['total_error'] * (20 + (kii ** 4) * 1e-8) \
                                          + 0.1 / (ind.f_values['distance'][d] + 2)

            # normalize rawfitness and add error to archive
            if max(all_archive_rawfitness) != 0:
                ind.f_archive_values['fitness'] = ind.f_archive_values['rawfitness'] / max(all_archive_rawfitness) \
                                                  + ind.f_archive_values['total_error'] * (20 + (kii ** 4) * 1e-8) \
                                                  + 0.1 / (ind.f_archive_values['distance'][d] + 2)
            else:
                ind.f_archive_values['fitness'] = ind.f_archive_values['total_error'] * (20 + (kii ** 4) * 1e-8) \
                                                  + 0.1 / (ind.f_archive_values['distance'][d] + 2)




    def calculate_error(self):

        pm_error = [0] * N
        power_error = [0] * N
        area_error = [0] * N

        for i, ind in enumerate(self.individuals):
            if ind.pm < min_pm:
                pm_error[i] = abs(min_pm - ind.pm) / min_pm

            if ind.power > max_power:
                power_error[i] = abs(max_power - ind.power) / max_power

            if ind.area > max_area:
                area_error[i] = abs(max_area - ind.area) / max_area

            ind.f_values['total_error'] = \
                pm_error[i] + power_error[i] + area_error[i]

    def enviromental1(self):

        for ind in self.individuals:
            if (ind.f_values['rawfitness'] == 0 and
                    ind.f_values['total_error'] == 0):
                self.archive_inds.append(ind)

        sorted_inds = sorted(self.individuals,
                             key=lambda x: x.f_values['fitness'])

        while len(self.archive_inds) < N:
            for ind in sorted_inds:
                if ind.f_values['rawfitness'] > 0 and \
                        ind.f_values['total_error']:
                    self.archive_inds.append(ind)

    def mating(self):

        matingpool = []
        for i in range(N // 2):
            p1 = math.ceil(randrange(N + 1))
            p2 = math.ceil(randrange(N + 1))

            while p1 == p2:
                p2 = math.ceil(randrange(N + 1))

            parent1 = self.archive_inds[p1]
            parent2 = self.archive_inds[p2]

            if parent1.f_values['fitness'] > parent2.f_values['fitness']:
                matingpool.append(parent2)
            else:
                matingpool.append(parent1)

            if len(matingpool) > 1:
                for ind in matingpool[:-1]:
                    if ind == matingpool[-1]:
                        p2 = math.ceil(randrange(N + 1))
                        parent2 = self.archive_inds[p2]
                        matingpool[-1] = parent2

        return matingpool

    def cross_mutation(self, matingpool):

        recombination_coefficient = [0.8] * N
        mutationStepSize = [0.1 + 0.2 * uniform(0, 1)
                            for _ in range(N)]

        child_parameters = []
        for i in range(0, N, 2):
            p1 = randrange(0, N // 2)
            p2 = randrange(0, N // 2)

            while p1 == p2:
                p2 = math.ceil(randrange(N + 1))

            ind_child1 = recombination_coefficient[i] * np.array(matingpool[p1].parameters) + \
                         ((1 - recombination_coefficient[i]) * np.array(matingpool[p2].parameters))
            child_parameters.append(ind_child1.tolist())

            ind_child2 = recombination_coefficient[i] * np.array(matingpool[p2].parameters) + \
                         ((1 - recombination_coefficient[i]) * np.array(matingpool[p1].parameters))
            child_parameters.append(ind_child2.tolist())

        mutation = [True if uniform(0, 1) > mut else False
                    for mut in mutationStepSize]

        for i, boolean in enumerate(mutation):
            if boolean:
                param_index_to_be_mutated = randrange(0, p)
                child_parameters[i][param_index_to_be_mutated] = \
                    lower_bound[param_index_to_be_mutated] + \
                    (upper_bound[param_index_to_be_mutated] -
                     lower_bound[param_index_to_be_mutated]) * uniform(0, 1)

        for params in child_parameters:
            for i, param in enumerate(params):
                if param < lower_bound[i] or param > upper_bound[i]:
                    params[i] = \
                        (upper_bound[i] - lower_bound[i]) * uniform(0, 1) + lower_bound[i]

        return child_parameters


class Generations:
    def __init__(self):
        self.gens = []
        self.saturation_inds = []
        self.all_inds = []
        self.archive_parameters = []
        self.archive_bw = []
        self.archive_gaindb = []
        self.archive_gainmag = []
        self.archive_pm = []
        self.archive_power = []
        self.archive_area = []
        self.archive_fitness = []
        self.archive_rawfitness = []
        self.archive_total_error = []

    def append(self, generation):
        """ Add the last generation to Generations"""
        self.gens.append(generation)
        for ind in generation.individuals:
            self.all_inds.append(ind)
            if ind.saturation:
                self.saturation_inds.append(ind)

        if len(self.gens) == 1:
            self.archive_parameters.append([ind.parameters
                                            for ind in generation.archive_inds])
            self.archive_bw.append([ind.bw
                                    for ind in generation.archive_inds])
            self.archive_gaindb.append([ind.gaindb
                                        for ind in generation.archive_inds])
            self.archive_gainmag.append([ind.gainmag
                                         for ind in generation.archive_inds])
            self.archive_pm.append([ind.pm
                                    for ind in generation.archive_inds])
            self.archive_power.append([ind.power
                                       for ind in generation.archive_inds])
            self.archive_area.append([ind.area
                                      for ind in generation.archive_inds])
            self.archive_fitness.append([ind.f_values['fitness']
                                         for ind in generation.archive_inds])
            self.archive_rawfitness.append([ind.f_values['rawfitness']
                                            for ind in generation.archive_inds])
            self.archive_total_error.append([ind.f_values['total_error']
                                             for ind in generation.archive_inds])

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
