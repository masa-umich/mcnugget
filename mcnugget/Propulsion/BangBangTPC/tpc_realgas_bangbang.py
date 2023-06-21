import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
from pyfluids import Fluid, FluidsList, Input
from numpy import genfromtxt

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

# Initialize fluid variables
RP1 = Fuel(290)
LOx = Fluid(FluidsList.Oxygen).with_state(Input.pressure(500*6894.76),Input.temperature(-190))
N2 = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(4500*6894.76),Input.temperature(16.85))

# Target tank pressure
P_tank = 500*6894.76
Tank_psi = 500

# Estimated Cd and collapse factor
Cd = 0.61
Cf = 2.1

# mdots at T0 
mdot_F = 1.9967
mdot_L = 3.9934

# Temperature for isentropic calcs
T0 = 290

# vdots at T0
vdot_F = mdot_F/RP1.rho
vdot_L = mdot_L/LOx.density

# gamma (seems like it should be constant for the scope of the problem)
gamma = 1.4

# COPV pressure array
COPV = np.linspace(P_tank/(2/(gamma+1))**(gamma/(gamma-1)),4500*6894.76,1000)
COPV_psi = np.linspace(Tank_psi/(2/(gamma+1))**(gamma/(gamma-1)),4500,1000)

# isothermal curves, outputs in square inches
Isotherm_F = np.zeros(1000)
Isotherm_L = np.zeros(1000)

for x in range(1000):
    N2 = N2.with_state(Input.pressure(COPV[x]),Input.temperature(16.85))
    Isotherm_F[x] = mdot_F/(Cd*(gamma*N2.density*COPV[x]*(2/(gamma+1))**((gamma+1)/(gamma-1)))**(1/2))*1550
    Isotherm_L[x] = mdot_L/(Cd*(gamma*N2.density*COPV[x]*(2/(gamma+1))**((gamma+1)/(gamma-1)))**(1/2))*1550*Cf

# plot the ideal area isothermal curves
line_1 = plt.plot(COPV_psi,Isotherm_F,'-r',label='RP1')
line_2 = plt.plot(COPV_psi,Isotherm_L,'-b',label='LOx')
plt.legend()
plt.xlabel("COPV Pressure (psi)")
plt.ylabel("Area (in^2)")
plt.show()