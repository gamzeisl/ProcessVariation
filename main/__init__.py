# # Name of the circuit that you want to execute
#
# circuit_name = 'amp'
#
# # constraints
# constraints = {
#     'pm': ('min', 45),
#     'power': ('max', 1e-3),
#     'area': ('max', 5e-9),
# }
#
# # targets to be optimize
# targets = ('gaindb', 'bw')
#
# # normalize values for fitness method
# normalize = {
#     'gaindb': 1,
#     'bw': 1e+4
# }
#
# N = 100  # number of population
# gen_number = 100

################################################################

# Name of the circuit that you want to execute

circuit_name = 'comp'

# constraints
constraints = {
    'tdlay': ('max', 2e-9),
    'rsarea': ('max', 5e-10),
}

# targets to be optimize
targets = ('offset', 'avgpower')

# normalize values for fitness method
normalize = {
    'offset': 1,
    'avgpower': 1
}

N = 50  # number of population
gen_number = 100

