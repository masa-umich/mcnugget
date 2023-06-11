import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
from class_init import Fuel
import numpy as np
import pint

# Chamber Regen Analysis Code
# This will analyze the regenerative cooling circuit iteratively, dividing the liner into axial stations

# Effects being studied:
#   1. Axial Temperature Gradient
#   2. Fuel Heating
#   3. Radial Thermal Expansion
#   4. Regen Pressure Drop
#   5. Individual and Combined Stresses
#   5. Maximum Temperature
#   6. Convective Heat Transfer Coefficients and Maximum Heat-flux

# Regen Channel Inputs
rc = Regen_Channel() 
rc.L = 12 # in
rc.di = 0.07026355393 # m 
rc.do = 0.07091 # m 
rc.A = ((np.pi / 4) * rc.do ** 2) - ((np.pi / 4) * rc.di ** 2) # m^2
rc.dh = 2 * ((rc.do/2) - (rc.di/2)) # m
rc.e = 0.00005 # m 

# Liner Inputs
Liner = Liner() 
Liner.k = 0.28 # kW/mK
Liner.rho = 8.9 # g/cm^3
Liner.a = 0.000017 # K^-1
Liner.v = 0.3
Liner.E = 17560000 * 6895 # Pa 
Liner.ty = 29370 * 6895 # Pa 
Liner.di = 0.06797755393 # m
Liner.do = 0.07026355393 # meters
Liner.T = 300 # Initial Liner Temperature


# Hot Gas Inputs
hg = 0.9625 # kW/m^2K
qrad = 482 # kW/m^2
Tg = 3316 # K

# Station Setup
N = 100 # number of stations
dx = rc.L / N # Length of each station
x = np.linspace(0, rc.L, N) # Axial position of each station
Twc = np.zeros(N) # Coldwall Temperature at each station
Twh = np.zeros(N) # Hotwall Temperature at each station
rho = np.zeros(N) # Density at each station
u = np.zeros(N) # Viscosity at each station
k = np.zeros(N) # Conductivity at each station
cp = np.zeros(N) # Specific Heat Capacity at each station
v = np.zeros(N) # Velocity at each station
Re = np.zeros(N) # Reynolds number at each station
Pr =  np.zeros(N) # Renolds number at each station


# Initial Conditions
Coolant = Fuel(300) # Initial Coolant Condiditions
Twc = np.full(N, Liner.T) # Initial Station Temperatures
Twh = np.full(N, Liner.T) # Initial Station Temperatures
Nu = np.zeros(N) # Nusselt Number at each station
hc = np.zeros(N) # Cold Wall Convective Heat Transfer Coefficient at each station
ql = np.zeros(N) # Coldwall Heat Flux at each station
Tc = np.full(N, Liner.T) # Initial Coolant Temperature
# Engine Inputs
mdot = 2.124 # kg/s

# Initial Calculations
Liner.di * np.pi * dx  # Hotwall Area per Station
Liner.do * np.pi * dx  # Coldwall Area per Station
rc.k = rc.e / rc.di # Relative Roughness

# Iterative Simulation
Twc_eps = 0.1 # Coldwall Temperature Convergence Criteria
Twh_eps = 0.1 # Hotwall Temperature Convergence Criteria

for n in range(0, N): # Iterates through each station
    if True:
        Twh[n] = Twh[n-1]
        Twc[n] = Twc[n-1]
    break
Coolant.T = Tc # Sets Coolant Temperature to Station Temperature
np.put(rho, n, Coolant.rho)# Sets Density to Station Density
np.put(u, n, Coolant.u)# Sets Viscosity to Station Viscosity
np.put(k, n, Coolant.k)# Sets Conductivity to Station Conductivity
np.put(cp, n, Coolant.cp)# Sets Specific Heat Capacity to Station Specific Heat Capacity
np.put(v, n, mdot / (rho[n] * rc.A))# Sets Velocity to Station Velocity
np.put(Re, n, (rho[n] * v[n] * rc.dh) / u[n])# Sets Reynolds Number to Station Reynolds Number
np.put(Pr, n, (cp[n] * u[n] * rc.dh) / k[n])# Sets Prandtl Number to Station Prandtl Number
Twc_prev = 0
Twh_prev = 0
print(Re[n])
while np.absolute(Twc[n]-Twc_prev) > Twc_eps and np.absolute(Twh[n]-Twh_prev) > Twh_eps:
    Twc_prev = Twc[n]
    Twh_prev = Twh[n]
    def ColbrookWhite(Re, k, dh):
        a = 0.01
        b = 0.05
        c = (a + b) / 2
        while np.absolute((1 / np.sqrt(c)) + (2 * np.log10((rc.k / (3.7 * rc.dh)) + (2.51 / (Re * np.sqrt(c)))))) > 0.0001:
            if (1 / np.sqrt(c)) + (2 * np.log10((rc.k / (3.7 * rc.dh)) + (2.51 / (Re * np.sqrt(c))))) < 0 and (1 / np.sqrt(a)) + (2 * np.log10((rc.k / (3.7 * rc.dh)) + (2.51 / (Re * np.sqrt(a))))) < 0:
                a = c
            else:
                b = c
                break
            c = (a + b) / 2
        return c
    rc.f = ColbrookWhite(Re[n], rc.k, rc.dh) # Sets Friction Factor 
    Nu[n] = ((rc.f / 8) * (Re[n] - 1000) * Pr[n]) / (1 + (12.7 * np.sqrt(rc.f / 8) * (np.power(Pr[n], (2/3)) - 1))) * (1 + ((Liner.do / Liner.di) ** 0.7)) # Sets Nusselt Number to Station Nusselt Number
    hc[n] = (Nu[n] * k[n]) / rc.dh # Sets Cold Wall Heat Transfer Coefficient
    ql[n] = hc[n] * (Twc[n] - Tc[n]) # Sets Cold Wall Heat Flux
    break





