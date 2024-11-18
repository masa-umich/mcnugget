import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from dataclasses import dataclass
from constants import *


@dataclass
class StateVector:
    p0: float
    rho: float
    T0: float
    vel: float
    nu: float  # Dynamic viscosity


def generate_data_csv():
    with open('regen_gap_data.txt', 'r') as file:
        data_1, data_2 = [], []
        count = 0
        for _, line in enumerate(file.readlines()):
            if line[0] == '#':
                continue
            a = [float(x) for x in line.split()]
            if count < 3:
                a = np.multiply(a, 25.4)
                data_1.append(a)
            elif count == 3:
                data_2.append(a)
            elif count > 3:
                a = np.divide(a, 1000)
                data_2.append(a)
            count += 1
        df_1 = pd.DataFrame(np.asarray(data_1))
        df_2 = pd.DataFrame(np.asarray(data_2))
        df_1.to_csv('regen_gap_data.csv', index=False, header=False)
        df_2.to_csv('regen_gap_data.csv', mode='a', index=False, header=False)


class RegenChannel:
    """
    Reads data from regen_gap_data.csv and generates interpolation curves so you can
    get the heat flux and positional information given an input of x position along
    the regen circuit.
    """
    def __init__(self, n: int = 100, csv_name: str = 'regen_gap_data.csv'):
        with open(csv_name, 'r') as csv_file:
            # All distances in millimeters, heat flux is in W/mm^2
            pos_measured = [float(x) for x in csv_file.readline().split(',')]
            self.x_min, self.x_max = 0, max(pos_measured)
            radius =       [float(x) for x in csv_file.readline().split(',')]
            height =       [float(x) for x in csv_file.readline().split(',')]
            self.get_radius = interp1d(pos_measured, radius, kind='linear')
            self.get_height = interp1d(pos_measured, height, kind='linear')
            pos_heat_flux = [float(x) for x in csv_file.readline().split(',')]
            heat_flux =     [float(x) for x in csv_file.readline().split(',')]
            self.get_heat_flux = interp1d(pos_heat_flux, heat_flux, kind='linear')
        # Define boundary conditions
        self.out_p0 = 360.3 * PSI_TO_PA  # Outlet stagnation pressure [Pa]
        self.in_p0 = 3e6  # Upstream total pressure [Pa]
        self.stations = np.linspace(self.x_min, self.x_max, n)
        self.ds = (self.x_max - self.x_min)/(n-1)  # Length of a station [mm]
        self.c_width = .104 * 25.4  # Single channel width [mm]
        self.num_c = 78  # Number of channels
        self.mdot = 2.06 / self.num_c  # Per channel total fuel mass flow rate [kg/s]
        # Preemptively solve for wattage at each station, per channel
        transfer_area = np.pi * np.square(self.get_radius(regen.stations)) / self.num_c
        self.heat_xfer_rate = self.get_heat_flux(self.get_radius) * transfer_area


class Solver():
    def __init__(self, regen: RegenChannel):
        self.regen = regen

    def solve(self):
        """Solve the system."""
        state_vec = StateVector(regen.in_p0, )
        for i, station in enumerate(self.regen.stations):
            pass


if __name__ == "__main__":
    generate_data_csv()
    regen = RegenChannel(n=1000)
    gap_width = 0.001 * 25.4
    solver = Solver(regen)
    solver.solve()
    plt.plot(regen.stations, regen.get_radius(regen.stations))
    plt.grid(True)
    plt.ylabel('Axial distance [mm]')
    plt.show()
