import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
from class_init import Fuel
from Colbrook_White import Friction_Factor
import numpy as np

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



# Regen Channel Inputs: 
# Geometric Properties of the Regen Channel

# - Outer Radius, Inner Radius
rc = Regen_Channel(0.07091, 0.07026355393)

# - L : Length of the Regen Channel
rc.L = 12 / 39.37 # m

# - e : Abolsute Roughness of the Regen Channel
rc.e = 0.00005 # m



# Liner Inputs: 
# Thermo-Physcial Properties of the Liner

# Liner Geometry
# - Outer Radius, Inner Radius
Liner = Liner(0.07026355393, 0.06797755393)


# Liner Material Properties Inputs: 
# - k: Thermal Conductivity
Liner.k = 280 # W/mK
# - rho: Density
Liner.rho = 8.9 # g/cm^3
# - a: Thermal Expansion Coefficient
Liner.a = 0.000017 # K^-1
# - v: Poisson's Ratio
Liner.v = 0.3
# - E: Young's Modulus
Liner.E = 17560000 * 6895 # Pa 
# - ty: Yield Strength
Liner.ty = 29370 * 6895 # Pa 
# - Initial Temperature
Liner.T = 300 # K



# Hot Gas Inputs:
# Heat transfer properties of the hot gas and radiation 
# - hg: Hot Gas Convective Heat Transfer Coefficient
hg = 962.5 # W/m^2K

# - qrad: Radiative Heat Flux
qrad = 0 # kW/m^2

# - Tg: Hot Gas Temperature
Tg = 3316 # K

# Engine Inputs:
# - mdot: Fuel Mass Flow Rate of the Engine
mdot = 2.124 # kg/s



# Station Setup:
# Initializes the stations and array of values at each station


# Station Geometry:
# - N: Number of Stations
N = 100 

# - dx: Axial Distance between each station
dx = rc.L / N 

# - x: Axial Position of each station
x = np.linspace(0, rc.L, N)

# - sA: Surface Area of the Hotwall at each station
Liner.sA = 2 * Liner.ri * np.pi * dx

# - sA: Surface Area of the Coldwall at each station
rc.sA = 2 * Liner.ro * np.pi * dx  # Coldwall Area per Station

# - A_lm: Log Mean Area between the Hotwall and Coldwall
A_lm = ((2 * np.pi * dx * Liner.ro) - (2 * np.pi * dx * Liner.ri)) / (np.log((2 * np.pi * dx * Liner.ro) / (2 * np.pi * dx * Liner.ri)))


# Temperature Stations
# - Twc: Coldwall Temperature at each station
Twc = np.zeros(N)

# - Twh: Hotwall Temperature at each station
Twh = np.zeros(N)


# Fluid Stations
# - rho: Density at each station
rho = np.zeros(N)

# - u: Viscosity at each station
u = np.zeros(N)

# - k: Conductivity at each station
k = np.zeros(N)

# - cp: Specific Heat Capacity at each station
cp = np.zeros(N)

# - v: Velocity at each station
v = np.zeros(N)

# - Re: Reynolds Number at each station
Re = np.zeros(N)

# - Pr: Prandtl Number at each station
Pr =  np.zeros(N)


# Heat Transfer Stations
# - f: Friction Factor at each station
f =  np.zeros(N)

# - Nu: Nusselt Number at each station
Nu = np.zeros(N) # Nusselt Number at each station

# - hc: Cold Wall Convective Heat Transfer Coefficient at each station
hc = np.zeros(N) # Cold Wall Convective Heat Transfer Coefficient at each station

# - Coldwall Heat Flux at each station
ql = np.zeros(N) 

# - Q: Heat Flow-rate at each station
Q = np.zeros(N) # Heat Flowrate at each station


# Initial Conditions
# - Initializes Coldwall Temperature
Twc = np.full(N, Liner.T)

# - Initializes Hotwall Temperature
Twh = np.full(N, Liner.T)

# - Initializes Coolant Temperature
Tc = Liner.T
Coolant = Fuel(Tc)

# - Calculates Relative Roughness of the Regen Channel
rc.k = rc.e / (2 * rc.ri)



# Iterative Simulation
# - Iterates through each station
print("")
print("Starting Iterative Simulation")
print("")
print("Twh, Twc, Tc, Nu, v, Re, Pr, f, n")

for n in range(0, N): 

    # Updates Station Coolant Values
    Coolant.T = Tc 
    np.put(rho, n, Coolant.rho)
    np.put(u, n, Coolant.u)
    np.put(k, n, Coolant.k)
    np.put(cp, n, Coolant.cp)
    np.put(v, n, mdot / (rho[n] * rc.A))
    np.put(Re, n, (rho[n] * v[n] * rc.dh) / u[n])
    np.put(Pr, n, (cp[n] * u[n]) / k[n])

    # Solves for friction factor using Colbrook-White Equation
    np.put(f, n, Friction_Factor(Re[n], rc.k))

    # Solves Steady State Heat Equation for the Wall Temperatures
    # - Calculates Nusselt Number and Updates the Station Values
    np.put(Nu, n, ((f[n] / 8) * (Re[n] - 1000) * Pr[n]) / (1 + (12.7 * np.sqrt(f[n] / 8) * (np.power(Pr[n], (2/3)) - 1)))) 

    # - Calculates Coldwall Heat Transfer Coefficient and Updates the Station Values
    np.put(hc, n, (Nu[n] * k[n]) / rc.dh) 

    # - Calculates Heat Flowrate and Updates the Station Values 
    np.put(Q, n, ((((1 / (hg * Liner.sA)) + ((Liner.ro - Liner.ri) / (Liner.k * A_lm)) + (1 / (hc[n] * rc.sA)))**(-1)) * (Tg - Tc))) 

    # - Calculates the Hotwall Temperature and Updates the Station Values
    np.put(Twh, n, -(Q[n] / (Liner.sA * hg)) + Tg) 

    # - Calculates the Coldwall Temperature and Updates the Station Values
    np.put(Twc, n, (-((Q[n] * (np.log(Liner.ro / Liner.ri)))) / (2 * np.pi * Liner.k * dx)) + Twh[n]) 

    # - Calculates the Final Coolant Temperature and Updates the Station Values
    Tc = Tc + Q[n] / (mdot * cp[n]) 

    # - Prints the Station Values and Iteration Number
    print(Twh[n], Twc[n], Tc, Nu[n], v[n], Re[n], Pr[n], f[n], n) 

print("")
print("End of Simulation!")
print("")
print("Maximum Hotwall Temperature [K], Maximum Coldwall Temperature [K], and Maximum Coolant Temperature [K]")
print(Twh[0], Twc[0], Tc)
print("")
print("Axial Gradient of Wall Temperature [K], Axial Gradient of Velocity [m/s], and Axial Gradient of Fuel Temperature [K]")
print((Twh[99]-Twh[0]), (v[99]-v[0]), (Tc - Liner.T))
print("")
