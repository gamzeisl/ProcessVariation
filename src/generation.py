import sobol_seq
import numpy as np
import pickle
import os
import math
import time
import itertools
import importlib

from threading import Thread
from matplotlib import pyplot as plt
from datetime import datetime
from random import randrange, uniform

from .population import Population
from mains import circuit_name, constraints, normalize, targets

circuit_module_path = "CircuitFiles." + circuit_name

cct_vars = importlib.import_module(circuit_module_path)


# from CircuitFiles import *


class Generation:
    def __init__(self, N: int):
        self.individuals = []
        self.properties = {
            'N': N, 'p': cct_vars.p, 'o': cct_vars.o, 'd': cct_vars.d, 'transistor_count': cct_vars.transistor_count,
            'lower_bound': cct_vars.lower_bound, 'upper_bound': cct_vars.upper_bound}
        self.constraints = constraints
        self.normalize = normalize
        self.targets = targets
        self.archive_inds = []
        self.sat_individuals = []

    def constraint_checker(self, ind: Population, key: str):

        if self.constraints.get(key)[0] == 'min':
            if getattr(ind, key) < self.constraints.get(key)[1]:
                return abs(self.constraints.get(key)[1] - getattr(ind, key)) / self.constraints.get(key)[1]
            return 0

        elif self.constraints.get(key)[0] == 'max':
            if getattr(ind, key) > self.constraints.get(key)[1]:
                return abs(self.constraints.get(key)[1] - getattr(ind, key)) / self.constraints.get(key)[1]
            return 0

        else:
            raise ValueError(f"Unrecognized constraint.")

    def population_initialize(self):
        dif_bound = (np.array(self.properties['upper_bound']) -
                     np.array(self.properties['lower_bound']))

        variable = np.multiply(dif_bound, np.random.rand(self.properties['N'], self.properties['p'])) \
                   + np.array(self.properties['lower_bound'])

        for var in variable:
            self.individuals.append(Population(var.tolist()))

    @classmethod
    def new_generation(cls, parameters: 'list of lists', n: int):

        gen = Generation(n)
        for params in parameters:
            ind = Population(params)
            gen.individuals.append(ind)

        return gen

    def simulate(self, multithread=None):
        """ Simulate each individual inside the generation """
        if multithread:
            cycle = self.properties['N'] // multithread
            remainder = self.properties['N'] % multithread
            lengths_to_split = [multithread] * cycle + [remainder]
            grouped_inds = [self.individuals[x - y: x] for x, y in zip(
                itertools.accumulate(lengths_to_split), lengths_to_split)]

            for group in grouped_inds:
                threads = []
                for i, ind in enumerate(group):
                    t = Thread(target=ind.simulate, args=str(i))
                    t.start()
                    threads.append(t)
                for thread in threads:
                    thread.join()

        else:
            for ind in self.individuals:
                ind.simulate('0')

        for ind in self.individuals:
            if ind.saturation:
                self.sat_individuals.append(ind)

    def plot_scatter_arch(self, gaintype: str = None, color='b', gen=None):
        """ Plot the generation """
        if gaintype == 'db':
            gain = [ind.gaindb for ind in self.archive_inds]
        elif gaintype == 'mag':
            gain = [ind.gainmag for ind in self.archive_inds]
        else:
            raise ValueError(f"gaintype should be db or mag")

        tar1 = [ind.target1 for ind in self.archive_inds]
        tar2 = [ind.target2 for ind in self.archive_inds]

        if color == 'alternate':
            color = np.random.rand(3, )

        if gen:
            plt.scatter(tar1, tar2, color=color, label=str(gen))
            plt.legend(loc='upper right', numpoints=1, ncol=5, fontsize=5)
        else:
            plt.scatter(tar1, tar2, color=color)

        plt.xlabel(self.targets[0])
        plt.ylabel(self.targets[1])

        plt.draw()
        plt.pause(0.001)

    def fitness_first(self):
        """ Assign fitness values to the first generation"""
        d = self.properties['d']
        target1_normalize = self.normalize.get(self.targets[0])
        target2_normalize = self.normalize.get(self.targets[1])

        self.calculate_error()

        # assign strength, distance and rawfitness to each individuals
        for ind1 in self.individuals:
            for j, ind2 in enumerate(self.individuals):

                if ind1.target1 > ind2.target1 and ind1.target2 > ind2.target2:
                    ind1.f_values['strength'] += 1

                elif ind1.target1 < ind2.target1 and ind1.target2 < ind2.target2:
                    ind1.f_values['rawfitness'] += 1

                ind1.f_values.get('distance')[j] = math.sqrt(
                    ((ind1.target1 - ind2.target1) / target1_normalize) ** 2 +
                    ((ind1.target2 - ind2.target2) / target2_normalize) ** 2)

            ind1.f_values['distance'].sort()

        rawfitnesses = [ind.f_values['rawfitness']
                        for ind in self.individuals]

        for i, ind in enumerate(self.individuals):
            ind.f_values['fitness'] = \
                ind.f_values['rawfitness'] / max(rawfitnesses) + \
                ind.f_values['total_error'] * 20 + 1 / (ind.f_values.get('distance')[d] + 2)

    def fitness(self, before_generation, kii):
        """ Assign fitness values to the generation except the first."""
        d = self.properties['d']
        target1_normalize = self.normalize.get(self.targets[0])
        target2_normalize = self.normalize.get(self.targets[1])

        self.calculate_error()

        # error between last and current generation
        relative_constraint_errors = [[0.0 for _ in range(self.properties['N'])]
                                      for _ in range(len(self.constraints))]
        relative_total_error = [0.0] * self.properties['N']

        for i, arch_ind_before in enumerate(before_generation.archive_inds):

            for constN, key in enumerate(self.constraints):
                relative_constraint_errors[constN][i] = self.constraint_checker(arch_ind_before, key)

            for constN in range(len(self.constraints)):
                relative_total_error[i] += relative_constraint_errors[constN][i]

        # Assign strength values to new generation
        for ind1 in self.individuals:
            for j, ind2 in enumerate(self.individuals):

                if ind1.target1 > ind2.target1 and ind1.target2 > ind2.target2:
                    ind1.f_values['strength'] += 1

                if ind1.target1 > before_generation.archive_inds[j].target1 and \
                        ind1.target2 > before_generation.archive_inds[j].target2:
                    ind1.f_values['strength'] += 1

        relative_strength = [0.00] * self.properties['N']
        # Assign strength values to archive
        for i, arch_ind_before in enumerate(before_generation.archive_inds):
            for j, ind in enumerate(self.individuals):

                if arch_ind_before.target1 > ind.target1 and arch_ind_before.target2 > ind.target2:
                    relative_strength[i] += 1

                if arch_ind_before.target1 > before_generation.archive_inds[j].target1 and \
                        arch_ind_before.target2 > before_generation.archive_inds[j].target2:
                    relative_strength[i] += 1

        # Assign rawfitness values to new generation
        for ind1 in self.individuals:
            for j, ind2 in enumerate(self.individuals):

                if ind1.target1 < ind2.target1 and ind1.target2 < ind2.target2:
                    ind1.f_values['rawfitness'] += ind2.f_values['strength']

                if ind1.target1 < before_generation.archive_inds[j].target1 and \
                        ind1.target2 < before_generation.archive_inds[j].target2:
                    ind1.f_values['rawfitness'] += relative_strength[j]

        relative_rawfitness = [0.00] * self.properties['N']
        # Assign rawfitness values to archive
        for i, arch_ind_before in enumerate(before_generation.archive_inds):
            for j, ind in enumerate(self.individuals):

                if arch_ind_before.target1 < ind.target1 and arch_ind_before.target2 < ind.target2:
                    relative_rawfitness[i] += ind.f_values['strength']

                if arch_ind_before.target1 < before_generation.archive_inds[j].target1 and \
                        arch_ind_before.target2 < before_generation.archive_inds[j].target2:
                    relative_rawfitness[i] += relative_strength[j]

        relative_fitness = [0.0] * self.properties['N']
        relative_distance = [[0.0 for _ in range(self.properties['N'])]
                             for _ in range(self.properties['N'])]
        for i, ind in enumerate(self.individuals):

            # Calculate distance values
            for j, arch_ind_before in enumerate(before_generation.archive_inds):
                ind.f_values['distance'][j] = math.sqrt(
                    ((ind.target1 - arch_ind_before.target1) / target1_normalize) ** 2 +
                    ((ind.target2 - arch_ind_before.target2) / target2_normalize) ** 2)

                relative_distance[i][j] = math.sqrt(
                    ((before_generation.archive_inds[i].target1 -
                      before_generation.archive_inds[j].target1) / target1_normalize) ** 2 +
                    ((before_generation.archive_inds[i].target2 -
                      before_generation.archive_inds[j].target2) / target2_normalize) ** 2)

            all_rawfitness = [ind.f_values['rawfitness']
                              for ind in self.individuals]

            ind.f_values['distance'].sort()
            relative_distance[i].sort()

            # normalize rawfitness and add error to generation
            if max(all_rawfitness) != 0:
                ind.f_values['fitness'] = ind.f_values['rawfitness'] / max(all_rawfitness) \
                                          + ind.f_values['total_error'] * (20 + (kii ** 4) * 1e-8) \
                                          + 0.1 / (ind.f_values['distance'][d] + 2)
            else:
                ind.f_values['fitness'] = ind.f_values['total_error'] * (20 + (kii ** 4) * 1e-8) \
                                          + 0.1 / (ind.f_values['distance'][d] + 2)

            # normalize rawfitness and add error to archive
            if max(relative_rawfitness) != 0:
                relative_fitness[i] = relative_rawfitness[i] / max(relative_rawfitness) \
                                      + relative_total_error[i] * (20 + (kii ** 4) * 1e-8) \
                                      + 0.1 / (relative_distance[i][d] + 2)
            else:
                relative_fitness[i] = relative_total_error[i] * (20 + (kii ** 4) * 1e-8) \
                                      + 0.1 / (relative_distance[i][d] + 2)

        # These are the values of the before
        # generation relative to the current generation
        return relative_fitness, relative_distance, relative_rawfitness, relative_total_error

    def calculate_error(self):

        const_errors = [[0.0 for _ in range(self.properties['N'])]
                        for _ in range(len(self.constraints))]

        for i, ind in enumerate(self.individuals):

            for constN, key in enumerate(self.constraints):
                const_errors[constN][i] = self.constraint_checker(ind, key)

            for constN in range(len(self.constraints)):
                ind.f_values['total_error'] += const_errors[constN][i]

    def enviromental(self, before_generation, archive_fitness,
                     archive_rawfitness, archive_total_error):

        archive_inds_temp = []
        for i, ind in enumerate(self.individuals):

            if ind.f_values['rawfitness'] == 0 and ind.f_values['total_error'] == 0:
                if ind not in archive_inds_temp:
                    archive_inds_temp.append(ind)

            if archive_rawfitness[i] == 0 and archive_total_error[i] == 0:
                if before_generation.archive_inds[i] not in archive_inds_temp:
                    archive_inds_temp.append(before_generation.archive_inds[i])

        all_fitness_temp = [ind.f_values['fitness']
                            for ind in self.individuals] + archive_fitness

        all_rawfitness_temp = [ind.f_values['rawfitness']
                               for ind in self.individuals] + archive_rawfitness

        all_total_error_temp = [ind.f_values['total_error']
                                for ind in self.individuals] + archive_total_error

        indexes = sorted(range(len(all_fitness_temp)),
                         key=lambda k: all_fitness_temp[k])

        all_fitness_temp, all_rawfitness_temp, all_total_error_temp = zip(
            *sorted(zip(all_fitness_temp, all_rawfitness_temp, all_total_error_temp), key=lambda x: x[0]))

        if len(archive_inds_temp) < self.properties['N']:

            i = 0
            while len(archive_inds_temp) < self.properties['N']:
                if indexes[i] < self.properties['N']:
                    if self.individuals[indexes[i]] not in archive_inds_temp:
                        archive_inds_temp.append(self.individuals[indexes[i]])
                else:
                    if before_generation.archive_inds[indexes[i] - self.properties['N']] not in archive_inds_temp:
                        archive_inds_temp.append(
                            before_generation.archive_inds[indexes[i] - self.properties['N']])
                i += 1

            self.archive_inds = archive_inds_temp[:]

        elif len(archive_inds_temp) > self.properties['N']:
            while len(archive_inds_temp) > self.properties['N']:
                del archive_inds_temp[-1]
            self.archive_inds = archive_inds_temp[:]
        else:
            self.archive_inds = archive_inds_temp[:]

    def mating(self):

        matingpool = []
        for i in range(self.properties['N'] // 2):
            p1 = math.ceil(randrange(self.properties['N']))
            p2 = math.ceil(randrange(self.properties['N']))

            while p1 == p2:
                p2 = math.ceil(randrange(self.properties['N']))

            parent1 = self.archive_inds[p1]
            parent2 = self.archive_inds[p2]

            if parent1.f_values['fitness'] > parent2.f_values['fitness']:
                matingpool.append(parent2)
            else:
                matingpool.append(parent1)

            if len(matingpool) > 1:
                for ind in matingpool[:-1]:
                    if ind == matingpool[-1]:
                        p2 = math.ceil(randrange(self.properties['N']))
                        parent2 = self.archive_inds[p2]
                        matingpool[-1] = parent2

        return matingpool

    def cross_mutation(self, matingpool):

        recombination_coefficient = [0.8] * self.properties['N']
        mutationStepSize = [0.1 + 0.2 * uniform(0, 1)
                            for _ in range(self.properties['N'])]

        child_parameters = []
        for i in range(0, self.properties['N'], 2):
            p1 = randrange(0, self.properties['N'] // 2)
            p2 = randrange(0, self.properties['N'] // 2)

            while p1 == p2:
                p2 = randrange(0, self.properties['N'] // 2)

            ind_child1 = recombination_coefficient[i] * np.array(matingpool[p1].parameters) + \
                         ((1 - recombination_coefficient[i]) * np.array(matingpool[p2].parameters))

            child_parameters.append(ind_child1.tolist())

            ind_child2 = recombination_coefficient[i] * np.array(matingpool[p2].parameters) + \
                         ((1 - recombination_coefficient[i]) * np.array(matingpool[p1].parameters))

            child_parameters.append(ind_child2.tolist())

        while len(child_parameters) > self.properties['N']:
            del child_parameters[-1]

        mutation = [True if uniform(0, 1) > mut else False
                    for mut in mutationStepSize]

        for i, boolean in enumerate(mutation):
            if boolean:
                param_index_to_be_mutated = randrange(0, self.properties['p'])
                child_parameters[i][param_index_to_be_mutated] = \
                    self.properties['lower_bound'][param_index_to_be_mutated] + \
                    (self.properties['upper_bound'][param_index_to_be_mutated] -
                     self.properties['lower_bound'][param_index_to_be_mutated]) * uniform(0, 1)

        for params in child_parameters:
            for i, param in enumerate(params):
                if param < self.properties['lower_bound'][i] or param > self.properties['upper_bound'][i]:
                    params[i] = \
                        (self.properties['upper_bound'][i] - self.properties['lower_bound'][i]) * uniform(0, 1) + \
                        self.properties['lower_bound'][i]

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

        # self.archive_parameters.append([ind.parameters
        #                                 for ind in generation.archive_inds])
        # self.archive_bw.append([ind.bw
        #                         for ind in generation.archive_inds])
        # self.archive_gaindb.append([ind.gaindb
        #                             for ind in generation.archive_inds])
        # self.archive_gainmag.append([ind.gainmag
        #                              for ind in generation.archive_inds])
        # self.archive_pm.append([ind.pm
        #                         for ind in generation.archive_inds])
        # self.archive_power.append([ind.power
        #                            for ind in generation.archive_inds])
        # self.archive_area.append([ind.area
        #                           for ind in generation.archive_inds])
        # self.archive_fitness.append([ind.f_values['fitness']
        #                              for ind in generation.archive_inds])
        # self.archive_rawfitness.append([ind.f_values['rawfitness']
        #                                 for ind in generation.archive_inds])
        # self.archive_total_error.append([ind.f_values['total_error']
        #                                  for ind in generation.archive_inds])

    def plot(self, start, stop, gaintype: str = None, color='b'):

        gens = self.gens[start:stop + 1]
        i = start
        for gen in gens:
            gen.plot_scatter_arch(gaintype=gaintype, color=color, gen=i)
            i += 1

    def save(self, start: int,
             stop: int, file_name=None):

        if not file_name:
            today = datetime.now()
            file_name = today.strftime(circuit_name + " d-%Y.%m.%d h-%H.%M ")
            file_name += 'gen-' + str(start) + '-' + str(stop)
        else:
            if not isinstance(file_name, str):
                raise TypeError(f"File name should be in str type"
                                f"but given {type(file_name)}")
        os.chdir('./data')

        if not isinstance(start, int) or not isinstance(stop, int):
            raise TypeError(f"Stop or start indexes should be"
                            f"integer type")
        if start > stop:
            raise ValueError(f"Start index can not be higher"
                             f"than stop index")
        else:
            with open(file_name, 'wb') as f:
                pickle.dump(self, f)

        os.chdir(r'..\\')
