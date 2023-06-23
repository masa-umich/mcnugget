import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
from class_init import Fuel
from Colbrook_White import Friction_Factor
from Stress import radial_stress
from Stress import axial_stress
from Stress import von_mises
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

# Simulation Settings:
# - N: Number of Stations
N = 100 # Resolution gain over 100 stations is minimal
 

# Regen Channel Inputs: 
# Geometric Properties of the Regen Channel
Channel_Outer_Radius = 0.07087 # m
Channel_Inner_Radius = 0.07026446847 # m
Liner_Inner_Radius = 0.06797846847 # m


# Engine Inputs:
# - mdot: Fuel Mass Flow Rate of the Engine
mdot = 2.063 # kg/s

# - Chamber Pressure:
#Convert psi to Pa
P_c = 309.5 * 6895 # Pa

# - Coolant Pressure: 
P_f = 444.8 * 6895 # Pa


# Liner Inputs: 
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
hg = 0.7035 * 1000 # W/m^2K

# - hrad: Radiative Heat Transfer Coefficient
hrad = 190.9271576 # W/m^2K

# - Tg: Hot Gas Temperature
Tg = 3327.9631 # K



# Channel Geometry Calculations
# - Outer Radius, Inner Radius
Liner = Liner(Channel_Inner_Radius, Liner_Inner_Radius)

# - Outer Radius, Inner Radius
rc = Regen_Channel(Channel_Outer_Radius, Channel_Inner_Radius)

# - L : Length of the Regen Channel
rc.L = 11.9 / 39.37 # m

# - e : Abolsute Roughness of the Regen Channel
rc.e = 0.00005 # m



# Station Setup:
# Initializes the stations and array of values at each station


# Station Geometry:
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

# - dP: Pressure Drop at each station
dP = np.zeros(N)

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
print("Heatflow rate, Twh, Twc, Tc, Nu, v, Re, Pr, f, n")

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

    # Solves for Pressure Drop using Darcy-Weisbach Equation
    np.put(dP, n, (f[n] * (rho[n] / 2) * (np.power(v[n], 2) / rc.dh))*dx)

    # Solves Steady State Heat Equation for the Wall Temperatures
    # - Calculates Nusselt Number and Updates the Station Values
    np.put(Nu, n, ((f[n] / 8) * (Re[n] - 1000) * Pr[n]) / (1 + (12.7 * np.sqrt(f[n] / 8) * (np.power(Pr[n], (2/3)) - 1)))) 

    # - Calculates Coldwall Heat Transfer Coefficient and Updates the Station Values
    np.put(hc, n, (Nu[n] * k[n]) / rc.dh) 

    # - Calculates Heat Flowrate and Updates the Station Values 
    np.put(Q, n, ((((1 / ((hg + hrad) * Liner.sA)) + ((Liner.ro - Liner.ri) / (Liner.k * A_lm)) + (1 / (hc[n] * rc.sA)))**(-1)) * (Tg - Tc))) 

    # - Calculates the Hotwall Temperature and Updates the Station Values
    np.put(Twh, n, -(Q[n] / ((Liner.sA * (hg + hrad))) - Tg))

    # - Calculates the Coldwall Temperature and Updates the Station Values
    np.put(Twc, n, (-((Q[n] * (np.log(Liner.ro / Liner.ri)))) / (2 * np.pi * Liner.k * dx)) + Twh[n]) 

    # - Calculates the Final Coolant Temperature and Updates the Station Values
    Tc = Tc + Q[n] / (mdot * cp[n]) 

    # - Prints the Station Values and Iteration Number
    print(Q[n], Twh[n], Twc[n], Tc, hc[n], v[n], Re[n], Pr[n], f[n], n) 
    #print(x[n], hc[n], Tc)
    
# - Calculates the Total Pressure Drop
# - Convert Pa to psi
dP_Total = np.sum(dP) * 0.000145038

print("")
print("End of Simulation!")
print("")
print("Maximum Hotwall Temperature [K], Maximum Coldwall Temperature [K], Wall Temperature Gradient [K], and Maximum Fuel Temperature [K]")
print(Twh[0], Twc[0], (Twh[0] - Twc[0]), Tc)
print("")
print("Axial Gradient of Wall Temperature [K], Axial Gradient of Velocity [m/s], and Axial Gradient of Fuel Temperature [K]")
print((Twh[n]-Twh[0]), (v[n]-v[0]), (Tc - Liner.T))
print("")
print("Total Pressure Drop [psi]")
print(dP_Total)
print("")

# Structural Calculations
# - q_max: Calculates the Maximum Heat Flux
q_max = np.amax(Q) / Liner.sA 

# - Max_Stress: Calculates the Maximum Radial Stress
Max_Stress = -radial_stress(q_max, Liner.ro, Liner.ri, P_c, P_f, Liner.E, Liner.a, Liner.k, Liner.v)

# - SF: Calculates the Safety Factor to Yield
SF = np.absolute(Liner.ty / Max_Stress)

print("Maximum stress [psi]")
print(Max_Stress/ 6895)
print("")
print("Safety Factor to Yield")
print(SF)
print("")
