import numpy as np
import os
import control

from src import transistor_count, p, o, circuit_name


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
            self.Vthchange = Vthchange if Vthchange else [0] * transistor_count * 2

        self.properties = {
            'p': p, 'o': o, 'transistor_count': transistor_count}

    # def __repr__(self):
    #     return self.parameters



    def set_Vthchange(self, sigma=None, mu=None):
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

        # write paramaters to param file
        self._write_param()

        # perform simulation
        os.system(
            'start/min/wait C:\synopsys\Hspice_A-2008.03\BIN\hspicerf.exe ' + circuit_name + '.sp -o ' + circuit_name)

        # read ma0 and parse gain, bw, himg, hreal, tmp
        self._read_ma0()

        # read ma0 and parse power, area, temper
        self._read_mt0()

        # read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        # Vdsat, beta, gm, gds, gmb
        self._read_dp0()

        if all([region == 'saturation'
                    for region in self.t_values['o_region']]):
            self.saturation = True
        else:
            self.saturation = False

    def _write_param(self):
        """ Write parameters to param.cir file"""
        with open('param.cir', 'r') as f:
            lines = f.readlines()
            headers = []
            for line in lines[1:]:
                headers.append(line.split(' ')[1])

        with open('param.cir', 'w') as f:
            f.write('.PARAM\n')
            for header, parameter in zip(headers, self.parameters):
                f.write('+ ' + header + ' = ' + str(parameter) + '\n')

    def _write_geo(self):
        """ Write Vth changes to geo.txt file"""
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
        self.power = float(lines_list[0])
        self.area = float(lines_list[1])
        self.temper = float(lines_list[2])

    def _read_dp0(self):
        """
        Read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        Vdsat, beta, gm, gds, gmb for each transistor

        """
        Id = [0] * transistor_count
        Ibs = [0] * transistor_count
        Ibd = [0] * transistor_count
        Vgs = [0] * transistor_count
        Vds = [0] * transistor_count
        Vbs = [0] * transistor_count
        Vth = [0] * transistor_count
        Vdsat = [0] * transistor_count
        beta = [0] * transistor_count
        gm = [0] * transistor_count
        gds = [0] * transistor_count
        gmb = [0] * transistor_count


        o_region = ['saturation'] * transistor_count

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


# if __name__ == '__main__':
#     a = Population([1, 2, 3, 4, 5, 6])
#     a.simulate()
#     pass