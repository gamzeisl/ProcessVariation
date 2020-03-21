transistor_count = 6  # number of transistors
p = 7  # number of variables
N = 50  # number of population
gen_number = 5
L = 130 * 1e-9
o = 3  # number of output
d = 2   # kth distance
lower_bound = [L, L, L,
               5 * L, 5 * L, 5 * L,
               10e-6]
upper_bound = [10 * L, 10 * L, 10 * L,
               750 * L, 750 * L, 750 * L, 1e-3]

min_pm = 45
max_power = 1e-3
max_area = 5e-9

circuit_name = 'amp'
