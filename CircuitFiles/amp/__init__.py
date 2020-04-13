transistor_count = 6  # number of transistors

p = 7  # number of variables

L = 130 * 1e-9

o = 3  # number of output

d = 1  # kth distance

lower_bound = [L, L, L,
               5 * L, 5 * L, 5 * L,
               10e-6]

upper_bound = [10 * L, 10 * L, 10 * L,
               750 * L, 750 * L, 750 * L, 1e-3]

topology = ['LM1', 'LM2', 'LM3',
            'WM1', 'WM2', 'WM3',
            'Ib']

circuit_name = 'amp'
