transistor_count = 20  # number of transistors

p = 16  # number of variables

L = 130 * 1e-9

o = 3  # number of output

d = 1  # kth distance

lower_bound = [L, L, L, L, L, L, L, L,
              5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L]

upper_bound = [5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L,
              500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L]

topology = ['LM1', 'LM2', 'LM3', 'LM4', 'LM5', 'LM6', 'LM7', 'LM8',
            'WM1', 'WM2', 'WM3', 'WM4', 'WM5', 'WM6', 'WM7', 'WM8']

circuit_name = 'comp'
