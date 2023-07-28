import numpy as np
import matplotlib.pyplot as plt
from matplotlib import interactive
import scipy.optimize as sp
import CoolProp.CoolProp as CP
from pyfluids import Fluid, FluidsList, Input
from numpy import genfromtxt
interactive(True)

# TPC Orifice Area Calculator
# Calculates the area needed for both fuel and LOx side TPC for varying COPV Pressure
# using real-gas properties

# Situations being considered
#   1. Isothermal (slow blow-down)
#   2. Isentropic (most like real burn)

# Target tank pressure, and max pressure rate of change
P_Fuel_Tank = 506.889*6894.76
P_LOx_Tank = 506.9*6894.76
dpdt = 100*6894.76

# Estimated Orifice Cd, collapse factor, and orifice area
Cd = 0.61
Cf = 1.4
CdA_Valve = 0.75/(27.66)

# mdots out at T0, in kg/s
mdot_Fuel = 2.063
mdot_LOx = 4.125

# Ideal Gamma
gamma = 1.4

# COPV max and min pressures
COPV_max = 4500 * 6894.76
COPV_min = P_Fuel_Tank/(2/(gamma+1))**(gamma/(gamma-1))

# ISENTROPIC CALCS

# Area arrays for constant pressure and area needed to stay below 10 psi/valve actuation time rate of change, in in^2
Isentrope_F = np.zeros(1000)
Isentrope_L = np.zeros(1000)
Isoe_plus10_F = np.zeros(1000)
Isoe_plus10_L = np.zeros(1000)

# Pressure array to use for graphing (does not affect math), in psi
P_C = np.zeros(1000)

# Copy of the fuel class from Logan's chamber analysis scripts (thanks btw)

Conductivity = genfromtxt('Conductivity.csv', delimiter=',')
Heat_Capacity = genfromtxt('Heat_Capacity.csv', delimiter=',')

# Interopolates Fuel Properties at a given temperature
# Inputs: Temperature (K)
# Outputs: Conductivity, Viscosity, Prandtl Number, Specific Heat, Density
class Fuel:
    def __init__(self, T):
        self.T = T

    @property
    def T(self):
        return self._T

    @T.setter
    def T(self, T):
        self._T = T
        self.k = np.interp(T, Conductivity[:, 0], Conductivity[:, 1])
        self.u = np.exp(2.5585 + (-3.505 / (T / 273.15)) - (3.412 * np.log(T / 273.15)) + (2.1551 * (T / 273.15)**(-3.145))) * 0.0008
        self.cp = np.interp(T, Heat_Capacity[:, 0], Heat_Capacity[:, 1])
        self.rho = 287.67 * 0.53365**(-(1 + (1 - (T / 574.262))**0.6289))

# Initialize baseline fluid variables
RP1 = Fuel(290)

# vdots into tank at T0, in m^3/s
vdot_Fuel = mdot_Fuel/RP1.rho
vdot_LOx = mdot_LOx/1140

# initial volume of gas, in m^3
V0_Ullage = (45/1000) * 0.075
V_C = 26.6/1000

# Time Step
dt = 0.006

# Number of steps in outer loop
N = 1000

# Number of steps in inner loop
n = 100

# Initial COPV Properties
N2_C = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(4500*6894.76),Input.temperature(16.85))
entropy = N2_C.entropy
COPV_pressures = np.linspace(800*6894.76,4500*6894.76,N)

# Initial Fuel Ullage Gas Properties
N2_F = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_Fuel_Tank),Input.temperature(16.85))
Z_Fuel = N2_F.compressibility
T_Ullage_Fuel = N2_F.temperature + 273.15
R_Fuel = N2_F.pressure/(Z_Fuel * T_Ullage_Fuel * N2_F.density)
Fuel_gas_mdots = np.zeros(N)

# Initial Fuel Ullage Mass
m_Ullage_Fuel = V0_Ullage * N2_F.density
V_Ullage_Fuel = V0_Ullage
e_Ullage_Fuel = N2_F.internal_energy
E_Ullage_Fuel = e_Ullage_Fuel*m_Ullage_Fuel

# Initial LOx Ullage Gas Properties
N2_LOx = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_LOx_Tank),Input.temperature(16.85))
Z_LOx = N2_LOx.compressibility
T_Ullage_LOx = N2_LOx.temperature + 273.15
R_LOx = N2_LOx.pressure/(Z_LOx * T_Ullage_LOx * N2_LOx.density)
LOx_gas_mdots = np.zeros(N)

# Initial LOx Ullage Mass
m_Ullage_LOx = V0_Ullage * N2_LOx.density
V_Ullage_LOx = V0_Ullage
e_Ullage_LOx = N2_LOx.internal_energy
E_Ullage_LOx = e_Ullage_LOx*m_Ullage_LOx



for y in range(N):
    # Previous COPV state values
    E_C_prev = N2_C.internal_energy*N2_C.density*V_C
    m_C_prev = N2_C.density*V_C

    # Increment COPV state
    N2_C = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(COPV_pressures[(N-1)-y]),Input.entropy(entropy))
    m_C = N2_C.density*V_C
    E_C = N2_C.internal_energy*m_C

    # Change in mass and energy
    delta_m = m_C_prev - m_C
    delta_E = E_C_prev - E_C
    
    # Previous tank state values
    V_Ull_F_prev = V_Ullage_Fuel
    V_Ull_L_prev = V_Ullage_LOx
    E_Ull_F_prev = e_Ullage_Fuel*m_Ullage_Fuel
    E_Ull_L_prev = e_Ullage_LOx*m_Ullage_LOx
    m_Ull_F_prev = m_Ullage_Fuel
    m_Ull_L_prev = m_Ullage_LOx
    
    # set up needed values for inner loop, previous ullage volume gets used later
    # so I added a new variable so the previous value remains untouched
    Z_Fuel = N2_F.compressibility
    Z_LOx = N2_LOx.compressibility
    V_Ull_F_Loop = V_Ull_F_prev
    V_Ull_L_Loop = V_Ull_L_prev
    for z in range(n):
        # Solve the system for the fuel tank state, x[0] is volume, x[1] is mass, x[2] is mdot,
        # x[3] is temperature, x[4] is total energy, add 5 to each to get the LOx variables
        def state_func(x):
            return[x[0] - V_Ull_F_Loop - vdot_Fuel*dt,
                   x[1]*Z_Fuel*R_Fuel*x[3] - P_Fuel_Tank*x[0],
                   x[1] - m_Ull_F_prev - x[2]*dt,
                   x[3]*N2_F.specific_heat*x[1] - x[4] - P_Fuel_Tank*x[0],
                   x[4] - E_Ull_F_prev - x[2]*N2_C.enthalpy*dt + P_Fuel_Tank*vdot_Fuel*dt,
                   x[5] - V_Ull_L_Loop - vdot_LOx*dt,
                   x[6]*Z_LOx*R_LOx*x[8] - P_LOx_Tank*x[5],
                   x[6] - m_Ull_L_prev - x[7]*dt,
                   x[8]*N2_LOx.specific_heat*x[6] - x[9] - P_LOx_Tank*x[5],
                   x[9] - E_Ull_L_prev - x[7]*N2_C.enthalpy*dt + P_LOx_Tank*vdot_LOx*dt]
        state = sp.fsolve(state_func,[1,1,1,1,1,1,1,1,1,1])

        V_Ull_F_Loop = state[0]
        m_Ull_F_prev = state[1]
        Fuel_gas_mdots[(N-1)-y] = state[2]
        T_Ull_F_prev = state[3]
        E_Ull_F_prev = state[4]
        V_Ull_L_Loop = state[5]
        m_Ull_L_prev = state[6]
        LOx_gas_mdots[(N-1)-y] = Cf*state[7]
        T_Ull_L_prev = state[8]
        E_Ull_L_prev = state[9]
    
    # Proportion of mass and energy entering each ullage
    delta_m_fuelgas = delta_m*(Fuel_gas_mdots[(N-1)-y]/(Fuel_gas_mdots[(N-1)-y]+LOx_gas_mdots[(N-1)-y]))
    delta_m_LOxgas = delta_m*(LOx_gas_mdots[(N-1)-y]/(Fuel_gas_mdots[(N-1)-y]+LOx_gas_mdots[(N-1)-y]))
    delta_E_fuelgas = delta_E*(Fuel_gas_mdots[(N-1)-y]/(Fuel_gas_mdots[(N-1)-y]+LOx_gas_mdots[(N-1)-y]))
    delta_E_LOxgas = delta_E*(LOx_gas_mdots[(N-1)-y]/(Fuel_gas_mdots[(N-1)-y]+LOx_gas_mdots[(N-1)-y]))

    # New tank state values
    m_Ullage_Fuel = m_Ullage_Fuel + delta_m_fuelgas
    m_Ullage_LOx = m_Ullage_LOx + delta_m_LOxgas
    V_Ullage_Fuel = V_Ullage_Fuel + delta_m_fuelgas/N2_F.density
    V_Ullage_LOx = V_Ullage_LOx + delta_m_LOxgas/N2_LOx.density
    E_Ullage_Fuel = E_Ullage_Fuel + delta_E_fuelgas - P_Fuel_Tank*(V_Ullage_Fuel - V_Ull_F_prev)
    E_Ullage_LOx = E_Ullage_LOx + delta_E_LOxgas - ((Cf * delta_E_LOxgas) - delta_E_LOxgas) - P_LOx_Tank*(V_Ullage_LOx - V_Ull_L_prev)

    # New tank states
    e_Ullage_Fuel = E_Ullage_Fuel/m_Ullage_Fuel
    e_Ullage_LOx = E_Ullage_LOx/m_Ullage_LOx
    N2_F = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_Fuel_Tank),Input.internal_energy(e_Ullage_Fuel))
    N2_LOx = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_LOx_Tank),Input.internal_energy(e_Ullage_LOx))

    # Debug and/or area calcs here
    #print(Fuel_gas_mdots[(N-1)-y],LOx_gas_mdots[(N-1)-y],E_Ullage_Fuel+E_Ullage_LOx+E_C,m_Ullage_Fuel+m_Ullage_LOx+m_C,V_Ullage_Fuel,V_Ullage_LOx)
    print(Fuel_gas_mdots[(N-1)-y],LOx_gas_mdots[(N-1)-y],N2_C.pressure / 6894.76, E_Ullage_Fuel+E_Ullage_LOx+E_C)