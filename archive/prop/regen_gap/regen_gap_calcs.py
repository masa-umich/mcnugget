import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import least_squares
from dataclasses import dataclass
from constants import *


@dataclass
class StateVector:
    p0: float
    vel: float
    T: float
    rho: float
    nu: float  # Dynamic viscosity
    cp: float


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
            self.get_radius = interp1d(pos_measured, radius, kind='linear', fill_value="extrapolate")
            self.get_height = interp1d(pos_measured, height, kind='linear', fill_value="extrapolate")
            pos_heat_flux = [float(x) for x in csv_file.readline().split(',')]
            heat_flux =     [float(x) for x in csv_file.readline().split(',')]
            self.get_heat_flux = interp1d(pos_heat_flux, list(reversed(heat_flux)), kind='linear', fill_value="extrapolate")
        # Define boundary conditions
        self.out_p0 = 360.3 * PSI_TO_PA  # Outlet stagnation pressure [Pa]
        self.in_p0 = 3e6  # Upstream total pressure [Pa]
        self.in_rho = 804.59  # Upstream total density [kg/m^3]
        self.stations = np.linspace(self.x_min, self.x_max, n)
        self.ds = (self.x_max - self.x_min)/(n-1)  # Length of a station [mm]
        self.c_width = .104 * 25.4  # Single channel width [mm]
        self.num_c = 78  # Number of channels
        self.mdot = 2.06 / self.num_c  # Per channel total fuel mass flow rate [kg/s]
        # Preemptively solve for wattage at each station, per channel
        transfer_area = 2 * np.pi * self.get_radius(self.stations) * self.ds / self.num_c
        self.heat_xfer_rate = self.get_heat_flux(self.stations) * transfer_area  # [W, or J/s]


class RP1:
    T_C = [0, 293.76, 334.15, 373.42, 434.65, 1000]  # [K]
    C_measured = [2015-293.76*(2153-2015)/(334.15-293.76), 2015, 2153, 2305,
                  2531, 2531+(1000-434.65)*(2531-2305)/(434.65-373.42)]
    cp_interp = interp1d(T_C, C_measured, kind='linear', fill_value="extrapolate")

    @staticmethod
    def get_rho(T: float):
        """Get density [kg/m^3] as a function of temperature [K]."""
        return 287.67 * 0.53365 ** -(1+(1-T/574.262)**0.6289)
    
    @staticmethod
    def get_nu(T: float):
        """Get dynamic viscosity [Pa*s] as a function of temperature [K]."""
        new_T = T/273.15
        return 0.0008 * np.exp(2.5585 - (3.505/new_T) - 3.412*np.log(new_T) + 2.1551*new_T**(-3.145))
    
    @staticmethod
    def get_cp(T: float):
        """Get specific heat at constant pressure [J/kg/K] as a function of temperature [K]."""
        return RP1.cp_interp(T)
        


class Solver():
    def __init__(self, regen: RegenChannel):
        self.regen = regen

    def solve(self, gap_size: float):
        """Solve the system with the given regen gap width."""
        init_rho, init_p0, init_cp, init_T = self.regen.in_rho, self.regen.in_p0, 2015.0, 298.0
        state_vec = StateVector(init_p0, None, init_T, init_rho, 0.00174, init_cp)
        # First, get the initial condition
        init_guess = tuple((0.02, 0.006, 30, 2.99e6, 800, 31, 2018, 300))
        curr_A_c = self.regen.c_width * self.regen.get_height(self.regen.stations[0])
        const_params = tuple((state_vec, curr_A_c, gap_size*self.regen.ds, init_rho, init_p0, init_cp*init_T,
                              self.regen.heat_xfer_rate[0], self.regen.mdot))
        soln_bounds = ((0, 0, 0, 0, 0, 0, 0, 0), (np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf))
        results = least_squares(regen_system_eqns, init_guess, args=const_params, bounds=soln_bounds).x
        print(f'Mdot_1: {results[0]:.5f} kg/s | Mdot_2: {results[1]:.5f} kg/s')
        print(f'Inlet vel: {results[2]:.3f} m/s | Inlet P_static: {results[3]:.3f} Pa')
        print(f'Exit rho: {results[4]:.3f} kg/m^3 | Exit vel: {results[5]:.3f} m/s | Exit T: {results[-1]:.3f} K')
        # for i, station in enumerate(self.regen.stations):
        #     pass


def regen_system_eqns(params: tuple, *const_params: tuple):
    mdot_1, mdot_2, v_i, p_i, rho_e, v_e, cp_e, T_e = params
    prev_state, A_c, A_gap, rho_0, p_0, e_0, Q_dot, mdot_out = const_params
    A_c, A_gap = A_c*1e-6, A_gap*1e-6  # Convert all [mm^2] to [m^2]
    eqn1 = prev_state.rho * A_c * v_i - mdot_1
    eqn2 = 0.8 * A_gap * np.sqrt(2*rho_0*(p_0 - p_i)) - mdot_2
    eqn3 = (mdot_1 + mdot_2) - mdot_out
    eqn4 = (rho_e * A_c * v_e) - mdot_out
    eqn5 = (mdot_1*prev_state.cp*prev_state.T) + (mdot_1*e_0) + Q_dot - (mdot_out*cp_e*T_e) 
    eqn6 = p_i + 0.5*rho_0*(v_i**2) - prev_state.p0
    eqn7 = RP1.get_cp(T_e) - cp_e
    eqn8 = RP1.get_rho(T_e) - rho_e
    eqn9 = mdot_out*v_e - (mdot_1*v_i)
    return (eqn1, eqn2, eqn3, eqn4, eqn5, eqn6, eqn7, eqn8, eqn9)


if __name__ == "__main__":
    regen = RegenChannel(n=100)
    plt.plot(regen.stations, regen.get_radius(regen.stations), label='Radius [mm]')
    plt.plot(regen.stations, regen.get_height(regen.stations), label='Channel Height [mm]')
    plt.plot(regen.stations, regen.get_heat_flux(regen.stations), label='Heat Flux [W/mm^2]')
    plt.grid(True)
    plt.title('Phoenix TCA')
    plt.xlabel('Axial distance [mm]')
    plt.legend()
    plt.show()
    solver = Solver(regen)
    solver.solve(gap_size=0.001*25.4)
