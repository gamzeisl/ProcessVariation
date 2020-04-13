# from CircuitFiles import gen_number, N

from src.generation import Generations, Generation
from main import N, gen_number

kii = 1
generations = Generations()  # form a generations object
generation = Generation(N)  # form a generation with N individuals

# initialize the first generation
generation.population_initialize()
generation.simulate(multithread=8)
generation.fitness_first()

generation.archive_inds = generation.individuals

generation.plot_scatter_arch(gaintype='mag', color='b', gen=kii)

# append it to generations class
generations.append(generation)

# cross-mutate the generation
matingpool = generation.mating()
crossed_parameters = generation.cross_mutation(matingpool)

# form a new generation
generation = Generation.new_generation(crossed_parameters, N)

while kii < gen_number:

    kii += 1

    generation.simulate(multithread=8)

    archive_fitness, archive_distance, \
        archive_rawfitness, archive_total_error = generation.fitness(generations.gens[-1], kii)

    generation.enviromental(generations.gens[-1], archive_fitness,
                            archive_rawfitness, archive_total_error)

    generation.plot_scatter_arch(gaintype='mag', color='alternate', gen=kii)

    generations.append(generation)
    matingpool = generation.mating()
    crossed_parameters = generation.cross_mutation(matingpool)
    generation = Generation.new_generation(crossed_parameters, N)

generations.save(0, 100)
