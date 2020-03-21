from src.generation import Generations, Generation
from src import gen_number, N


kii = 0
generations = Generations()  # form a generations object
generation = Generation(N)  # form a generation with N individuals

# initialize the first generation
generation.population_initialize()
generation.simulate()
generation.plot_scatter(gaintype='mag', color='b')
generation.fitness1()
generation.enviromental1()


generations.append(generation)

while kii < gen_number:
    # generation = generations.new_generation()

    pass
