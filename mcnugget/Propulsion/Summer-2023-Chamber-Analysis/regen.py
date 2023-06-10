import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
from class_init import fuel
import numpy as np
import pint
from fuel import fuel_prop

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

# Regen Channel Parameters
rc = Regen_Channel() 
rc.L = 12 # in
rc.di = 0.07091 # m 
rc.do = 0.07026355393 # m 
rc.A = ((np.pi / 4) * rc.do ** 2) - ((np.pi / 4) * rc.di ** 2) # m^2
rc.dh = 2 * ((rc.do/2) - (rc.di/2)) # m

# Liner Parameters
Liner = Liner() 
k = 0.28 # kW/mK
rho = 8.9 # g/cm^3
a = 0.000017 # K^-1
v = 0.3
E = 17560000 * 6895 # Pa 
ty = 29370 * 6895 # Pa 
di = 0.06797755393 # m
do = 0.07026355393 # meters
