import numpy as np
import matplotlib.pyplot as plt
from matplotlib import interactive
import scipy.optimize as sp
import CoolProp.CoolProp as CP
from pyfluids import Fluid, FluidsList, Input
from numpy import genfromtxt
#interactive(True)

# TPC Orifice Area Calculator
# Calculates the area needed for both fuel and LOx side TPC for varying COPV Pressure
# using real-gas properties

# Number of steps in outer loop
N = 1000

# Number of steps in inner loop
n = 100

# Target tank pressure, and max pressure rate of change
P_Fuel_Tank = 506.889*6894.76
P_LOx_Tank = 506.9*6894.76
dpdt = 100*6894.76

# Estimated Orifice Cd, collapse factor, and orifice area
Cd = 0.61
Cf = 1.5
CdA_Valve = 0.75/(27.66)

# mdots out at T0, in kg/s
mdot_Fuel = 2.063
mdot_LOx = 4.125

# Array for gamma
gamma = 1.4

# COPV max and min pressures
COPV_max = 4000 * 6894.76
COPV_min = P_Fuel_Tank/(2/(gamma+1))**(gamma/(gamma-1))

# ISENTROPIC CALCS

# Area arrays for constant pressure and area needed to stay below 10 psi/valve actuation time rate of change, in in^2
Isentrope_F = np.zeros(N)
Isentrope_L = np.zeros(N)
Isoe_plus10_F = np.zeros(N)
Isoe_plus10_L = np.zeros(N)

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
V0_Ullage_F = (55.44/1000)*0.075
V0_Ullage_L = (72.37/1000)*0.075
V_C = 26.6/1000

# Time Step
dt = 0.006

# Initial COPV Properties
N2_C = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(4000*6894.76),Input.temperature(16.85))
entropy = N2_C.entropy
COPV_pressures = np.linspace(1500*6894.76,4000*6894.76,N)

# Initial Fuel Ullage Gas Properties
N2_F = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_Fuel_Tank),Input.temperature(16.85))
Z_Fuel = N2_F.compressibility
T_Ullage_Fuel = N2_F.temperature + 273.15
R_Fuel = N2_F.pressure/(Z_Fuel * T_Ullage_Fuel * N2_F.density)
Fuel_gas_mdots = np.zeros(N)

# Initial Fuel Ullage Mass
m_Ullage_Fuel = V0_Ullage_F * N2_F.density
V_Ullage_Fuel = V0_Ullage_F
e_Ullage_Fuel = N2_F.internal_energy
E_Ullage_Fuel = e_Ullage_Fuel*m_Ullage_Fuel

# Initial LOx Ullage Gas Properties
N2_LOx = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(P_LOx_Tank),Input.temperature(160 - 273.15))
Z_LOx = N2_LOx.compressibility
T_Ullage_LOx = N2_LOx.temperature + 273.15
R_LOx = N2_LOx.pressure/(Z_LOx * T_Ullage_LOx * N2_LOx.density)
LOx_gas_mdots = np.zeros(N)

# Initial LOx Ullage Mass
m_Ullage_LOx = V0_Ullage_L * N2_LOx.density
V_Ullage_LOx = V0_Ullage_L
e_Ullage_LOx = N2_LOx.internal_energy
E_Ullage_LOx = e_Ullage_LOx*m_Ullage_LOx

time_elapsed = 0

# IDEAL GAS CALCULATION
print("IDEAL GAS CALCS")
R_N2 = 296.80
C_mdot = Cd * N2_C.pressure * (gamma/(R_N2*290))**0.5 * (2/(gamma+1))**((gamma+1)/(2*(gamma-1)))
Area_Init_Fuel = (0*V0_Ullage_F + vdot_Fuel*P_Fuel_Tank)/(C_mdot*R_N2*290)*1550
Area_Init_LOx = Cf*(0*V0_Ullage_L + vdot_LOx*P_LOx_Tank)/(C_mdot*R_N2*160)*1550
A_max_F = (dpdt*V0_Ullage_F + vdot_Fuel*P_Fuel_Tank)/(C_mdot*R_N2*290)*1550
A_max_L = Cf*(dpdt*V0_Ullage_L + vdot_LOx*P_LOx_Tank)/(C_mdot*R_N2*160)*1550
print("Ideal Initial Orifice Areas")
print("Fuel:", Area_Init_Fuel, "in^2")
print("LOx: ", Area_Init_LOx, "in^2")
print("Maximum Initial Orifice Areas")
print("Fuel:", A_max_F, "in^2")
print("LOx:",A_max_L, "in^2")

# COOLPROP LOOP CALCULATION

for y in range(N):
    # Previous COPV state values
    E_C_prev = N2_C.internal_energy*N2_C.density*V_C
    m_C_prev = N2_C.density*V_C

    # Increment COPV state
    N2_C = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(COPV_pressures[(N-1)-y]),Input.entropy(entropy))
    m_C = N2_C.density*V_C
    E_C = N2_C.internal_energy*m_C

    P_C[(N-1)-y] = N2_C.pressure/6894.76
    #gamma = N2_C.enthalpy/N2_C.internal_energy

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

    delta_t = delta_m_fuelgas/Fuel_gas_mdots[(N-1)-y]
    time_elapsed = time_elapsed + delta_t

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
    #print(Fuel_gas_mdots[(N-1)-y],LOx_gas_mdots[(N-1)-y],N2_C.pressure / 6894.76, E_Ullage_Fuel+E_Ullage_LOx+E_C,gamma,N2_F.temperature + 237.15,N2_LOx.temperature + 273.15)

    C_mdot = (Cd*(gamma*N2_C.density*N2_C.pressure*(2/(gamma+1))**((gamma+1)/(gamma-1)))**0.5)
    Isentrope_F[(N-1)-y] = Fuel_gas_mdots[(N-1)-y] / C_mdot * 1550
    Isentrope_L[(N-1)-y] = LOx_gas_mdots[(N-1)-y] / C_mdot * 1550
    Isoe_plus10_F[(N-1)-y] = (dpdt*(V_Ullage_Fuel)**2 + (delta_m_fuelgas/N2_F.density/delta_t)*N2_F.pressure*V0_Ullage_F)/(C_mdot*R_Fuel*(N2_F.temperature + 273.15)*V0_Ullage_F*Z_Fuel) * 1550
    Isoe_plus10_L[(N-1)-y] = Cf*(dpdt*(V_Ullage_LOx)**2 + (delta_m_LOxgas/N2_LOx.density/delta_t)*N2_LOx.pressure*V0_Ullage_L)/(C_mdot*R_LOx*(N2_LOx.temperature + 273.15)*V0_Ullage_L*Z_LOx) * 1550

# graph fuel orifice area
plt.figure(1)
ideal_fuel = plt.plot(P_C,Isentrope_F,'-r',label='MINIMUM AREA')
plus_10_F = plt.plot(P_C,Isoe_plus10_F,'--r',label='MAXIMUM AREA')
quarter_valve = plt.plot([P_C[0],P_C[N-1]],[0.25*CdA_Valve,0.25*CdA_Valve],'-g',label='1/4 Tescom')
half_valve = plt.plot([P_C[0],P_C[N-1]],[0.5*CdA_Valve,0.5*CdA_Valve],'-g',label='1/2 Tescom')
threequart_valve = one_valve = plt.plot([P_C[0],P_C[N-1]],[0.75*CdA_Valve,0.75*CdA_Valve],'-g',label='3/4 Tescom')
plt.ylim([0,0.03])
plt.xlabel("COPV Pressure (psi)")
plt.ylabel("Orifice Area (in^2)")
plt.title("Fuel TPC Area")
plt.legend()

# graph LOx orifice area
plt.figure(2)
ideal_LOx = plt.plot(P_C,Isentrope_L,'-b',label='MINIMUM AREA')
plus_10_L = plt.plot(P_C,Isoe_plus10_L,'--b',label='MAXIMUM AREA')
one_valve = plt.plot([P_C[0],P_C[N-1]],[CdA_Valve,CdA_Valve],'-g',label='1 Tescom')
two_valve = plt.plot([P_C[0],P_C[N-1]],[2*CdA_Valve,2*CdA_Valve],'-g',label='2 Tescoms')
three_valve = plt.plot([P_C[0],P_C[N-1]],[3*CdA_Valve,3*CdA_Valve],'-g',label='3 Tescoms')
plt.ylim([0,0.1])
plt.xlabel("COPV Pressure (psi)")
plt.ylabel("Orifice Area (in^2)")
plt.title("LOx TPC Area")
plt.legend()

plt.show()