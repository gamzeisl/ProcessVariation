from src.generation import Generations

transistor_count = 6  # number of transistors
p = 14  # number of variables
N = 200  # number of population
gen_number = 100
L = 130 * 1e-9
o = 4  # number of output
lower_bound = [L, L, L, L, L, L, L, L,
               5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L]
upper_bound = [5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L,
               500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L]

circuit_name = 'amp'


