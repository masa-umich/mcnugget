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
Cf = 2.1
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

# Initial COPV Properties
N2_C = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(4500*6894.76),Input.temperature(16.85))
entropy = N2_C.entropy

# Initial Fuel Ullage Gas Properties
N2_F = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_Fuel_Tank),Input.temperature(16.85))
Z_Fuel = N2_F.compressibility
T_Ullage_Fuel = N2_F.temperature + 273.15
R_Fuel = N2_F.pressure/(Z_Fuel * T_Ullage_Fuel * N2_F.density)

# Initial Fuel Ullage Mass
m_Ullage_Fuel = V0_Ullage * N2_F.density
V_Ullage_Fuel = V0_Ullage
e_Ullage_Fuel = N2_F.internal_energy

# Initial LOx Ullage Gas Properties
N2_LOx = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_LOx_Tank),Input.temperature(16.85))
Z_LOx = N2_LOx.compressibility
T_Ullage_LOx = N2_LOx.temperature + 273.15
R_LOx = N2_LOx.pressure/(Z_LOx * T_Ullage_LOx * N2_LOx.density)

# Initial LOx Ullage Mass
m_Ullage_LOx = V0_Ullage * N2_LOx.density
V_Ullage_LOx = V0_Ullage
e_Ullage_LOx = N2_LOx.internal_energy

# Solve the system for the fuel tank state, x[0] is volume, x[1] is mass, x[2] is mdot,
# x[3] is temperature, x[4] is total energy
for y in range(1000):
    Z_Fuel = N2_F.pressure / (N2_F.density * R_Fuel * (N2_F.temperature + 273.15))
    def fuelFunc(x):
        return [x[0] - V_Ullage_Fuel - vdot_Fuel * dt,
                (x[1] * x[3] * Z_Fuel * R_Fuel) - (P_Fuel_Tank * x[0]),
                x[1] - m_Ullage_Fuel - (x[2] * dt),
                (x[3] * N2_F.specific_heat * x[1]) - x[4] - (P_Fuel_Tank * x[0]),
                x[4] - (e_Ullage_Fuel * m_Ullage_Fuel) - (x[2] * N2_C.enthalpy * dt) + (P_Fuel_Tank * vdot_Fuel * dt)]
    Fuel_state = sp.fsolve(fuelFunc,[1,1,1,1,1])
    V_Ullage_Fuel = Fuel_state[0]
    m_Ullage_Fuel = Fuel_state[1]
    mdot_gas_Fuel = Fuel_state[2]
    T_Ullage_Fuel = Fuel_state[3]
    e_Ullage_Fuel = Fuel_state[4]
    e_Ullage_Fuel = e_Ullage_Fuel / m_Ullage_Fuel
    rho_Ullage_Fuel = m_Ullage_Fuel / V_Ullage_Fuel
    N2_F = Fluid(FluidsList.Nitrogen).with_state(Input.density(rho_Ullage_Fuel),Input.temperature(T_Ullage_Fuel - 273.15))
    P_Fuel_Tank = N2_F.pressure

    # Solve the system for the LOx tank state, x[0] is volume, x[1] is mass, x[2] is mdot,
    # x[3] is temperature, x[4] is total energy
    Z_LOx = N2_LOx.pressure / (N2_LOx.density * R_LOx * (N2_LOx.temperature + 273.15))
    def LOxFunc(y):
        return [y[0] - V_Ullage_LOx - vdot_LOx * dt,
                (y[1] * y[3] * Z_LOx * R_LOx) - (P_LOx_Tank * y[0]),
                y[1] - m_Ullage_LOx - (y[2] * dt),
                (y[3] * N2_LOx.specific_heat * y[1]) - y[4] - (P_LOx_Tank * y[0]),
                y[4] - (e_Ullage_LOx * m_Ullage_LOx) - (y[2] * N2_C.enthalpy * dt) + (P_LOx_Tank * vdot_LOx * dt)]
    LOx_state = sp.fsolve(LOxFunc,[1,1,1,1,1])
    V_Ullage_LOx = LOx_state[0]
    m_Ullage_LOx = LOx_state[1]
    mdot_gas_LOx = LOx_state[2]
    T_Ullage_LOx = LOx_state[3]
    e_Ullage_LOx = LOx_state[4]
    e_Ullage_LOx = e_Ullage_LOx / m_Ullage_LOx
    rho_Ullage_LOx = m_Ullage_LOx / V_Ullage_LOx
    N2_LOx = Fluid(FluidsList.Nitrogen).with_state(Input.density(rho_Ullage_LOx),Input.temperature(T_Ullage_LOx - 273.15))
    P_LOx_Tank = N2_LOx.pressure

    # Increment the COPV state
    #enthalpy = N2_C.enthalpy - ((mdot_gas_Fuel + mdot_gas_LOx) * dt * N2_C.enthalpy)
    #N2_C = N2_C.with_state(Input.enthalpy(enthalpy), Input.entropy(entropy))
    rho_C = ((N2_C.density * V_C) - ((mdot_gas_Fuel + mdot_gas_LOx) * dt)) / V_C
    N2_C = N2_C.with_state(Input.density(rho_C), Input.entropy(N2_C.entropy))
    Z_C = N2_C.compressibility
    T_C = N2_C.temperature + 273.15
    R_C = N2_C.pressure/(Z_C * T_C * N2_C.density)
    gammaC = N2_C.specific_heat/(N2_C.specific_heat-R_C)
    print(N2_C.pressure/6894.76, N2_C.temperature + 273.15, N2_C.enthalpy, mdot_gas_Fuel, mdot_gas_LOx)

    # Area calculation for current COPV pressure
    P_C[y] = N2_C.pressure/6894.76
    Isentrope_F[y] = mdot_gas_Fuel/(Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isentrope_L[y] = mdot_gas_LOx/(Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550*Cf
    Isoe_plus10_F[y] = (dpdt*V_Ullage_Fuel**2 + V_Ullage_Fuel*P_Fuel_Tank*vdot_Fuel)/(V_Ullage_Fuel*R_Fuel*T_Ullage_Fuel*Z_Fuel*Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isoe_plus10_L[y] = (dpdt*V_Ullage_LOx**2 + V_Ullage_LOx*P_LOx_Tank*vdot_LOx)/(V_Ullage_LOx*R_LOx*T_Ullage_LOx*Z_LOx*Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550*Cf