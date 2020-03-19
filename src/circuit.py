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

circuit_name = 'amp'


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

        self.properties = {
            'N': N, 'p': p, 'o': o, 'transistor_count': transistor_count}

    def set_Vth(self, sigma=None, mu=None):
        """
        Assigns Vthchange values to every transistor in an individual

        :param sigma: deviation for gaussian
        :param mu: mean value for gaussian
        """
        pass

    def plot(self, save=False):
        """
        Plot the indiviual
        if save=True saves it into src file

        """
        pass

    def simulate(self):

        path = '../CircuitFiles/'
        os.chdir(path)

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
            'start/min/wait C:\synopsys\Hspice_A-2008.03\BIN\hspicerf.exe ' + circuit_name + '.sp -o ' + circuit_name)
        # os.chdir('../src')

        # read ma0 and parse gain, bw, himg, hreal, tmp
        self._read_ma0()

        # read ma0 and parse power, area, temper
        self._read_mt0()

        # read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        # Vdsat, beta, gm, gds, gmb
        self._read_dp0()

    def _write_geo(self):
        with open('geo.txt', 'w') as f:
            f.write('.PARAM\n')
            for i, elem in enumerate(self.Vthchange):
                f.write('+ ' + 'dvtg' + str(i) + ' = ' + str(elem) + '\n')

    def _read_ma0(self):
        """ Read gain, bw, himg, hreal, tmp"""
        with open(circuit_name + '.ma0', 'r') as f:
            lines = f.readlines()
        lines_list = lines[3].split()

        self.bw = abs(float(lines_list[0]))
        self.gaindb = abs(float(lines_list[1]))
        himg = float(lines_list[2])
        hreal = float(lines_list[3])

        if himg > 0 and hreal > 0:
            self.pm = np.arctan(himg / hreal) * 180 / np.pi
        elif himg > 0 and hreal < 0:
            self.pm = 180 - np.arctan(himg / hreal) * 180 / np.pi
        elif himg < 0 and hreal < 0:
            self.pm = np.arctan(himg / hreal) * 180 / np.pi
        else:
            self.pm = 10

        self.tmp = lines_list[4]

    def _read_mt0(self):
        """ Read power, area, temper"""
        with open(circuit_name + '.mt0', 'r') as f:
            lines = f.readlines()
        lines_list = lines[3].split()
        self.power = lines_list[0]
        self.area = lines_list[1]
        self.temper = lines_list[2]

    def _read_dp0(self):
        """
        Read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        Vdsat, beta, gm, gds, gmb for each transistor

        """
        Id, Ibs, Ibd, Vgs, Vds, \
        Vbs, Vth, Vdsat, beta, \
        gm, gds, gmb = [[0.00] * transistor_count] * 12

        with open(circuit_name + '.dp0', 'r') as f:
            lines = f.readlines()

        row_list = [line.split('|') for line in lines
                    if '|' in line]
        row_list = [[elem.strip() for elem in row
                     if not elem == '']
                    for row in row_list]

        transistor_names = ['M' + str(x + 1) for x in range(transistor_count)]

        for rowN, row in enumerate(row_list):
            for colN, elem in enumerate(row):
                if elem in transistor_names:
                    transN = int(elem[-1])
                    Id[transN - 1] = float(row_list[rowN + 4][colN])
                    Ibs[transN - 1] = float(row_list[rowN + 5][colN])
                    Ibd[transN - 1] = float(row_list[rowN + 6][colN])
                    Vgs[transN - 1] = float(row_list[rowN + 7][colN])
                    Vds[transN - 1] = float(row_list[rowN + 8][colN])
                    Vbs[transN - 1] = float(row_list[rowN + 9][colN])
                    Vth[transN - 1] = float(row_list[rowN + 10][colN])
                    Vdsat[transN - 1] = float(row_list[rowN + 11][colN])
                    beta[transN - 1] = float(row_list[rowN + 12][colN])
                    gm[transN - 1] = float(row_list[rowN + 14][colN])
                    gds[transN - 1] = float(row_list[rowN + 15][colN])
                    gmb[transN - 1] = float(row_list[rowN + 16][colN])

        self.t_values = {'Id': Id, 'Ibs': Ibs, 'Ibd': Ibd,
                         'Vgs': Vgs, 'Vds': Vds, 'Vbs': Vbs,
                         'Vth': Vth, 'Vdsat': Vdsat, 'beta': beta,
                         'gm': gm, 'gds': gds, 'gmb': gmb}


    @property
    def gainmag(self):
        return control.db2mag(self.gaindb)

    @staticmethod
    def db2mag(x):
        return control.db2mag(x)

    @staticmethod
    def mag2db(x):
        return control.mag2db(x)


if __name__ == '__main__':
    a = Population([1, 2, 3, 4, 5, 6])
    a.simulate()
