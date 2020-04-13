import numpy as np
import os
import control
import importlib

from matplotlib import pyplot as plt
from main import circuit_name, N, targets

circuit_module_path = "CircuitFiles." + circuit_name

cct_vars = importlib.import_module(circuit_module_path)


class Population:
    def __init__(self, parameters: list, Vthchange=None):

        if not isinstance(parameters, list):
            raise TypeError(
                f"Parameters should be list of float!")
        else:
            self.parameters = parameters

        self.topology = cct_vars.topology

        self.properties = {
            'p': cct_vars.p, 'o': cct_vars.o, 'transistor_count': cct_vars.transistor_count,
            'N': N, 'circuit_name': circuit_name}

        self.f_values = {'total_error': 0.0, 'strength': 0.0,
                         'rawfitness': 0.0, 'distance': [0.0] * self.properties['N'],
                         'fitness': 0.0}

        self.targets = targets

        if Vthchange:
            if not isinstance(Vthchange, list):
                raise TypeError(
                    f"Vthchange should be list of float!")
            elif not len(Vthchange) == self.properties['transistor_count']:
                raise ValueError(
                    f"Size of Vthchange should be {self.properties['transistor_count']} "
                    f"but received {len(Vthchange)}")
            self.Vthchange = Vthchange

        else:
            self.Vthchange = Vthchange if Vthchange else [0] * self.properties['transistor_count'] * 2

    def __repr__(self):
        return ' , '.join([str(param) for param in self.parameters])

    @property
    def target1(self):
        if len(self.targets) >= 1:
            return getattr(self, self.targets[0])
        else:
            return None

    @property
    def target2(self):
        if len(self.targets) >= 2:
            return getattr(self, self.targets[1])
        else:
            return None

    @property
    def target3(self):
        if len(self.targets) >= 3:
            return getattr(self, self.targets[2])
        else:
            return None

    def set_Vthchange(self, sigma=None, mu=None):
        """
        Assigns Vthchange values to every transistor in an individual

        :param sigma: deviation for gaussian
        :param mu: mean value for gaussian

        """
        pass

    def plot(self, gaintype: str = None, color='b'):
        """
        Plot the indiviual
        if save=True saves it into src file

        """
        if gaintype == 'db':
            gain = self.gaindb
        elif gaintype == 'mag':
            gain = self.gainmag
        else:
            raise ValueError(f"gaintype should be db or mag")

        if color == 'alternate':
            color = np.random.rand(3, )

        plt.scatter(self.bw, gain, color=color)

        plt.draw()
        plt.pause(0.001)

    def simulate(self, file_no: str):

        path = os.getcwd() + r'\CircuitFiles\\' + self.properties['circuit_name'] + r'\\' + \
               self.properties['circuit_name'] + file_no + r'\\'

        # write Vth changes to geo.txt file
        self._write_geo(path)

        # write parameters to param file
        self._write_param(path)

        # perform simulation

        command = r'start/min/wait /D ' + path + r' C:\synopsys\Hspice_A-2008.03\BIN\hspicerf.exe ' \
                  + self.properties['circuit_name'] + '.sp -o ' + self.properties['circuit_name']

        os.system(command)

        # read ma0 and parse gain, bw, himg, hreal, tmp
        self._read_ma0(path)

        # read ma0 and parse power, area, temper
        self._read_mt0(path)

        # read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        # Vdsat, beta, gm, gds, gmb
        self._read_dp0(path)

        if all([region == 'saturation'
                for region in self.t_values['o_region']]):
            self.saturation = True
        else:
            self.saturation = False

    def _write_param(self, path):
        """ Write parameters to param.cir file"""

        with open(path + 'param.cir', 'w') as f:
            f.write('.PARAM\n')
            for header, parameter in zip(self.topology, self.parameters):
                f.write('+ ' + header + ' = ' + str(parameter) + '\n')

    def _write_geo(self, path):
        """ Write Vth changes to geo.txt file"""
        with open(path + 'geo.txt', 'w') as f:
            f.write('.PARAM\n')
            for i, elem in enumerate(self.Vthchange):
                f.write('+ ' + 'dvtg' + str(i) + ' = ' + str(elem) + '\n')

    def _read_ma0(self, path):
        """ Read gain, bw, himg, hreal, tmp"""
        try:
            with open(path + circuit_name + '.ma0', 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            return None

        lines_list = lines[3].split()

        self.bw = abs(float(lines_list[0]))
        self.gaindb = abs(float(lines_list[1]))
        himg = 0.0 if lines_list[2] == 'failed' else float(lines_list[2])
        hreal = 0.0 if lines_list[3] == 'failed' else float(lines_list[3])

        if himg > 0 and hreal > 0:
            self.pm = np.arctan(himg / hreal) * 180 / np.pi
        elif himg > 0 and hreal < 0:
            self.pm = 180 - np.arctan(himg / hreal) * 180 / np.pi
        elif himg < 0 and hreal < 0:
            self.pm = np.arctan(himg / hreal) * 180 / np.pi
        else:
            self.pm = 10

        self.tmp = lines_list[4]

    def _read_mt0(self, path):
        """ Read power, area, temper"""
        with open(path + circuit_name + '.mt0', 'r') as f:
            lines = f.readlines()

        headers_list = lines[2].split()
        lines_list = lines[3].split()

        for header, value in zip(headers_list, lines_list):
            if header == 'alter#':
                header = 'alter'

            try:
                value = float(value)
            except ValueError:
                print(f'cannot convert {value}')
                setattr(self, header, 0)
            else:
                setattr(self, header, value)

    def _read_dp0(self, path):
        """
        Read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        Vdsat, beta, gm, gds, gmb for each transistor

        """
        transistor_count = self.properties['transistor_count']
        Id = [0.00] * transistor_count
        Ibs = [0.00] * transistor_count
        Ibd = [0.00] * transistor_count
        Vgs = [0.00] * transistor_count
        Vds = [0.00] * transistor_count
        Vbs = [0.00] * transistor_count
        Vth = [0.00] * transistor_count
        Vdsat = [0.00] * transistor_count
        beta = [0.00] * transistor_count
        gm = [0.00] * transistor_count
        gds = [0.00] * transistor_count
        gmb = [0.00] * transistor_count

        o_region = ['saturation'] * transistor_count

        with open(path + circuit_name + '.dp0', 'r') as f:
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

                    if Vgs[transN - 1] < Vth[transN - 1] - 0.05:
                        o_region[transN - 1] = 'cutoff'
                    elif Vds[transN - 1] < (Vgs[transN - 1] - Vth[transN - 1] - 0.05):
                        o_region[transN - 1] = 'triode'

        self.t_values = {'Id': Id, 'Ibs': Ibs, 'Ibd': Ibd, 'Vgs': Vgs,
                         'Vds': Vds, 'Vbs': Vbs, 'Vth': Vth, 'Vdsat': Vdsat,
                         'beta': beta, 'gm': gm, 'gds': gds, 'gmb': gmb,
                         'o_region': o_region}

    @property
    def gainmag(self):
        if hasattr(self, 'gaindb'):
            return control.db2mag(self.gaindb)
        else:
            return None

    @staticmethod
    def db2mag(x):
        return control.db2mag(x)

    @staticmethod
    def mag2db(x):
        return control.mag2db(x)
