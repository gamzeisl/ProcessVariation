from CircuitFiles import gen_number, N
from generation import Generations, Generation

kii = 0
generations = Generations()  # form a generations object
generation = Generation(N)  # form a generation with N individuals

# initialize the first generation
generation.population_initialize()
generation.simulate()
generation.plot_scatter(gaintype='mag', color='b')
generation.fitness_first()
generation.enviromental_first()

# append it to generations class
generations.append(generation)

# cross-mutate the generation
matingpool = generation.mating()
crossed_parameters = generation.cross_mutation(matingpool)

# form a new generation
generation = Generation.new_generation(crossed_parameters, N)

while kii < gen_number:
    generation.simulate()
    generation.plot_scatter(gaintype='mag', color='alternate')

    archive_fitness, archive_distance, \
        archive_rawfitness, archive_total_error = generation.fitness(generations.gens[-1], kii)

    generation.enviromental(generations.gens[-1], archive_fitness,
                            archive_distance, archive_rawfitness,
                            archive_total_error)

    generations.append(generation)
    matingpool = generation.mating()
    crossed_parameters = generation.cross_mutation(matingpool)
    generation = Generation.new_generation(crossed_parameters, N)
    kii += 1
