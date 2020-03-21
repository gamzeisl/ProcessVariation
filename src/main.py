from src.generation import Generations, Generation
from src import gen_number, N
from random import randrange

kii = 0
generations = Generations()  # form a generations object
generation = Generation(N)  # form a generation with N individuals

# initialize the first generation
generation.population_initialize()
generation.simulate()
generation.plot_scatter(gaintype='mag', color='b')
generation.fitness1()
generation.enviromental1()

# append it to generations class
generations.append(generation)

# cross-mutate the generation
matingpool = generation.mating()
crossed_parameters = generation.cross_mutation(matingpool)

# form a new generation
generation = Generation.new_generation(crossed_parameters, N)

while kii < gen_number:
    generation.simulate()
    generation.plot_scatter(gaintype='mag', color=randrange(3))

    generation.fitness2(generations.gens[-1])

    generation.enviromental1()

