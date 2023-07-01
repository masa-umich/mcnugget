import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
from pyfluids import Fluid, FluidsList, Input
from numpy import genfromtxt

# TPC Orifice Area Calculator
# Calculates the area needed for both fuel and LOx side TPC for varying COPV Pressure
# using real-gas properties

# Situations being considered
#   1. Isothermal (slow blow-down, closest to ideal-gas calculator)
#   2. Isentropic (most like real burn)

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
N2_tank = Fluid(FluidsList.Nitrogen).with_state(Input.pressure(500*6894.76),Input.temperature(16.85))

# Target tank pressure, and max pressure rate of change
P_tank = 500*6894.76
Tank_psi = 500
dpdt = 100*6894.76

# Estimated Cd, collapse factor, and orifice area
Cd = 0.61
Cf = 2.1
A = 0.75/27.66

# mdots at T0 
mdot_F = 1.9967
mdot_L = 3.9934

# vdots into tank at T0
vdot_F = mdot_F/RP1.rho
vdot_L = mdot_L/LOx.density

# initial volume of gas
V0_F = 46.4/1000
V0_L = 29.5/1000

# gamma 
gamma = 1.4

# entropy at initial condisitons
entropy = N2.entropy

# COPV pressure array
COPV = np.linspace(P_tank/(2/(gamma+1))**(gamma/(gamma-1)),4500*6894.76,1000)
COPV_psi = np.linspace(Tank_psi/(2/(gamma+1))**(gamma/(gamma-1)),4500,1000)

# ISOTHERMAL CALCS
Isotherm_F = np.zeros(1000)
Isotherm_L = np.zeros(1000)
Isot_plus10_F = np.zeros(1000)
Isot_plus10_L = np.zeros(1000)

dt = 10/1000 # timestep size
P_C = np.zeros(1000)

N2_F = N2_tank.with_state(Input.pressure(P_tank),Input.temperature(16.85))
N2_L = N2_tank.with_state(Input.pressure(P_tank),Input.temperature(16.85))
N2_C = N2.with_state(Input.pressure(COPV[999]),Input.temperature(16.85))
V_C = 0.0266
Z_C = N2_C.compressibility
T_C = N2_C.temperature + 273.15
R_C = N2_C.pressure/(Z_C*N2_C.density*T_C)
gammaC = N2_C.specific_heat/(N2_C.specific_heat-R_C)
Z_F = N2_F.compressibility
Z_L = N2_L.compressibility
T_F = N2_F.temperature + 273.15
T_L = N2_L.temperature + 273.15
R_F = N2_F.pressure/(Z_F*T_F*N2_F.density)
R_L = N2_L.pressure/(Z_L*T_L*N2_L.density)
VF = V0_F
VL = V0_L
mF = N2_F.density*VF
mL = N2_L.density*VL
mdinF = vdot_F*N2_F.density
mdinL = vdot_L*N2_L.density*Cf

for x in range(1000):
    P_C[x] = N2_C.pressure/6894.76
    Isotherm_F[x] = mdinF/(Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isotherm_L[x] = mdinL/(Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isot_plus10_F[x] = (dpdt*VF**2 + V0_F*P_tank*vdot_F)/(V0_F*R_F*T_F*Z_F*Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isot_plus10_L[x] = (dpdt*VF**2 + V0_F*P_tank*vdot_L)/(V0_L*R_L*T_L*Z_L*Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550*Cf

    mF = mF + mdinF*dt
    mL = mL + mdinL*dt
    VF = VF + vdot_F*dt
    VL = VL + vdot_L*dt
    rhoF = mF/VF
    rhoL = mL/VL

    HdotF = vdot_F*(N2_F.density*N2_C.enthalpy )
    HdotL = vdot_L*(N2_L.density*N2_C.enthalpy )
    EdotF = HdotF - N2_F.pressure*vdot_F
    EdotL = HdotL - N2_L.pressure*vdot_L
    eF = (N2_F.internal_energy*mF + EdotF*dt)/mF
    eL = (N2_L.internal_energy*mL + EdotL*dt)/mL

    N2_F = N2_F.with_state(Input.internal_energy(eF),Input.density(rhoF))
    N2_L = N2_L.with_state(Input.internal_energy(eL),Input.density(rhoL))
    Z_F = N2_F.compressibility
    Z_L = N2_L.compressibility
    T_F = N2_F.temperature + 273.15
    T_L = N2_L.temperature + 273.15
    R_F = N2_F.pressure/(Z_F*T_F*N2_F.density)
    R_L = N2_L.pressure/(Z_L*T_L*N2_L.density)

    rhoC = (N2_C.density*V_C - (mdinF + mdinL)*dt)/V_C
    N2_C = N2_C.with_state(Input.density(rhoC),Input.temperature(16.85))
    Z_C = N2_C.compressibility
    T_C = N2_C.temperature + 273.15
    R_C = N2_C.pressure/(Z_C*N2_C.density*T_C)
    gammaC = N2_C.specific_heat/(N2_C.specific_heat-R_C)

    mdinF = vdot_F*N2_F.density
    mdinL = vdot_L*N2_L.density*Cf


# plot the isothermal curves
plt.figure(1)
line_1 = plt.plot(P_C,Isotherm_F,'-r',label='Constant Pressure')
line_2 = plt.plot(P_C,Isot_plus10_F,'--r',label='+10 psi')
line_3 = plt.plot([COPV_psi[0],COPV_psi[999]],[A,A],'-g',label='1 valve')
line_4 = plt.plot([COPV_psi[0],COPV_psi[999]],[2*A,2*A],'--g',label='2 valves')
plt.legend()
plt.title('Isothermal Fuel')
plt.xlabel("COPV Pressure (psi)")
plt.ylabel("Area (in^2)")

plt.figure(2)
line_1 = plt.plot(P_C,Isotherm_L,'-b',label='Constant Pressure')
line_2 = plt.plot(P_C,Isot_plus10_L,'--b',label='+10 psi')
line_3 = plt.plot([COPV_psi[0],COPV_psi[999]],[A,A],'-g',label='1 valve')
line_4 = plt.plot([COPV_psi[0],COPV_psi[999]],[2*A,2*A],'--g',label='2 valves')
plt.legend()
plt.title('Isothermal LOx')
plt.xlabel("COPV Pressure (psi)")
plt.ylabel("Area (in^2)")

# ISENTROPIC CALCS
Isentrope_F = np.zeros(1000)
Isentrope_L = np.zeros(1000)
Isoe_plus10_F = np.zeros(1000)
Isoe_plus10_L = np.zeros(1000)

# Reinitialize fluids and constants
dt = 10/1000 # timestep size
P_C = np.zeros(1000)

N2_F = N2_tank.with_state(Input.pressure(P_tank),Input.temperature(16.85))
N2_L = N2_tank.with_state(Input.pressure(P_tank),Input.temperature(16.85))
N2_C = N2.with_state(Input.pressure(COPV[999]),Input.entropy(entropy))
V_C = 0.0266
Z_C = N2_C.compressibility
T_C = N2_C.temperature + 273.15
R_C = N2_C.pressure/(Z_C*N2_C.density*T_C)
gammaC = N2_C.specific_heat/(N2_C.specific_heat-R_C)
Z_F = N2_F.compressibility
Z_L = N2_L.compressibility
T_F = N2_F.temperature + 273.15
T_L = N2_L.temperature + 273.15
R_F = N2_F.pressure/(Z_F*T_F*N2_F.density)
R_L = N2_L.pressure/(Z_L*T_L*N2_L.density)
VF = V0_F
VL = V0_L
mF = N2_F.density*VF
mL = N2_L.density*VL
mdinF = vdot_F*N2_F.density
mdinL = vdot_L*N2_L.density*Cf

for x in range(1000):
    #area calc from previous step
    P_C[x] = N2_C.pressure/6894.76
    Isentrope_F[x] = mdinF/(Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isentrope_L[x] = mdinL/(Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isoe_plus10_F[x] = (dpdt*VF**2 + V0_F*P_tank*vdot_F)/(V0_F*R_F*T_F*Z_F*Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550
    Isoe_plus10_L[x] = (dpdt*VF**2 + V0_F*P_tank*vdot_L)/(V0_L*R_L*T_L*Z_L*Cd*N2_C.pressure*((gammaC/(R_C*Z_C*T_C))*(2/(gammaC+1))**((gammaC+1)/(gammaC-1)))**0.5)*1550*Cf

    #increment tank mass and volume
    mF = mF + mdinF*dt
    mL = mL + mdinL*dt
    VF = VF + vdot_F*dt
    VL = VL + vdot_L*dt
    rhoF = mF/VF
    rhoL = mL/VL

    #increment gas internal energy
    HdotF = vdot_F*(N2_F.density*N2_C.enthalpy )
    HdotL = vdot_L*(N2_L.density*N2_C.enthalpy )
    EdotF = HdotF - N2_F.pressure*vdot_F
    EdotL = HdotL - N2_L.pressure*vdot_L
    eF = (N2_F.internal_energy*mF + EdotF*dt)/mF
    eL = (N2_L.internal_energy*mL + EdotL*dt)/mL

    #set new tank states
    N2_F = N2_F.with_state(Input.internal_energy(eF),Input.density(rhoF))
    N2_L = N2_L.with_state(Input.internal_energy(eL),Input.density(rhoL))
    Z_F = N2_F.compressibility
    Z_L = N2_L.compressibility
    T_F = N2_F.temperature + 273.15
    T_L = N2_L.temperature + 273.15
    R_F = N2_F.pressure/(Z_F*T_F*N2_F.density)
    R_L = N2_L.pressure/(Z_L*T_L*N2_L.density)

    #set new COPV state
    rhoC = (N2_C.density*V_C - (mdinF + mdinL)*dt)/V_C
    N2_C = N2_C.with_state(Input.density(rhoC),Input.entropy(entropy))
    Z_C = N2_C.compressibility
    T_C = N2_C.temperature + 273.15
    R_C = N2_C.pressure/(Z_C*N2_C.density*T_C)
    gammaC = N2_C.specific_heat/(N2_C.specific_heat-R_C)

    #get new tank mdots
    mdinF = vdot_F*N2_F.density
    mdinL = vdot_L*N2_L.density*Cf


# plot the isentropic curves
plt.figure(3)
line_1 = plt.plot(P_C,Isentrope_F,'-r',label='Constant Pressure')
line_2 = plt.plot(P_C,Isoe_plus10_F,'--r',label='+10 psi')
line_3 = plt.plot([COPV_psi[0],COPV_psi[999]],[A,A],'-g',label='1 valve')
line_4 = plt.plot([COPV_psi[0],COPV_psi[999]],[2*A,2*A],'--g',label='2 valves')
plt.legend()
plt.title('Isentropic Fuel')
plt.xlabel("COPV Pressure (psi)")
plt.ylabel("Area (in^2)")
plt.xlim([COPV_psi[0],COPV_psi[999]])
plt.ylim([0,0.1])

plt.figure(4)
line_1 = plt.plot(P_C,Isentrope_L,'-b',label='Constant Pressure')
line_2 = plt.plot(P_C,Isoe_plus10_L,'--b',label='+10 psi')
line_3 = plt.plot([COPV_psi[0],COPV_psi[999]],[A,A],'-g',label='1 valve')
line_4 = plt.plot([COPV_psi[0],COPV_psi[999]],[2*A,2*A],'--g',label='2 valves')
plt.legend()
plt.title('Isentropic LOx')
plt.xlabel("COPV Pressure (psi)")
plt.ylabel("Area (in^2)")
plt.xlim([COPV_psi[0],COPV_psi[999]])
plt.ylim([0,0.3])

plt.show()