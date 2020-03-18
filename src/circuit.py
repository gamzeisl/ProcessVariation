import numpy as np
import sobol_seq
import os
import control

transistor_count = 6  # number of transistors
p = 14  # number of variables
N = 200  # number of population
L = 130 * 1e-9
o = 4  # number of output
lower_bound = [L, L, L, L, L, L, L, L,
               5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L]
upper_bound = [5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L, 5 * L,
               500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L, 500 * L]


class Generation:
    def __init__(self):
        self.N = N
        self.p = p
        self.transistor_count = transistor_count
        self.o = o
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.individuals = []

    def population_initialize(self):
        for _ in range(self.N):
            qmc = sobol_seq.i4_sobol_generate(1, self.p)
            dif_bound = (np.array(self.upper_bound) - np.array(self.lower_bound))
            variable = list(np.multiply(dif_bound, qmc) + np.array(self.lower_bound))
            self.individuals.append(Population(variable))


class Population:
    def __init__(self, parameters: list, Vthchange=None):

        if not isinstance(parameters, list):
            raise TypeError(
                f"Parameters should be list of float!")
        else:
            self.parameters = parameters

        if Vthchange:
            if not isinstance(Vthchange, list):
                raise TypeError(
                    f"Vthchange should be list of float!")
            elif not len(Vthchange) == transistor_count:
                raise ValueError(
                    f"Size of Vthchange should be {transistor_count} "
                    f"but received {len(Vthchange)}")
            self.Vthchange = Vthchange
        else:
            self.Vthchange = Vthchange if Vthchange else [0] * transistor_count

        self.N = N
        self.p = p
        self.transistor_count = transistor_count
        self.o = o

    def set_Vth(self, sigma=None, mu=None):
        """
        Assigns Vthchange values to every transistor in an individual

        :param sigma: deviation for gaussian
        :param mu: mean value for gaussian
        """



    def simulate(self):

        path = '../CircuitFiles/'
        os.chdir(path)
        circuit_name = 'amp'

        # write Vth changes to geo.txt file
        self._write_geo()

        with open(path + 'designparam.cir', 'r') as f:
            lines = f.readlines()
            headers = []
            for line in lines[1:]:
                headers.append(line.split(' ')[1])

        with open(path + 'param.cir', 'w') as f:
            f.write('.PARAM\n')
            for header, parameter in zip(headers, self.parameters):
                f.write('+ ' + header + ' = ' + str(parameter) + '\n')

        os.system(
            'start/min/wait C:\synopsys\Hspice_A-2008.03\BIN\hspicerf.exe ' + folder_name + '.sp -o ' + folder_name)
        # os.chdir('../src')

        # read ma0 and parse gain, bw, himg, hreal, tmp
        self._read_ma0(circuit_name)
        # read ma0 and parse power, area, temper, alter
        self._read_ma0()

    def _write_geo(self):
        with open('geo.text', 'w') as f:
            f.write('.PARAM\n')
        for i, elem in enumerate(self.Vthchange):
            f.write('+ ' + 'dvtg' + str(i) + ' = ' + str(elem) + '\n')

    def _read_ma0(self, circuit_name):
        with open(circuit_name + '.text', 'r') as f:
            lines = f.readlines()
        lines_list = lines[3].split()
        self.bw = abs(float(lines_list[0]))
        self.gaindb = abs(float(lines_list[1]))
        self.gainmag = control.db2mag(self.gaindb)
        himg = float(lines_list[2])
        hreal = float(lines_list[3])
        # if himg > 0 and hreal > 0:
        #     pass
        # if li


    def _read_mt0(self):
        pass

    def _read_lis(self):
        pass

    @staticmethod
    def db2mag(x):
        return control.db2mag(x)

    @staticmethod
    def mag2db(x):
        return control.mag2db(x)

if __name__ == '__main__':
    a = Population([1, 2, 3, 4, 5, 6])
    # a.simulate()
    print(Population.mag2db()()
