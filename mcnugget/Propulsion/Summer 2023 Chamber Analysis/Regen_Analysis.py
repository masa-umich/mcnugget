import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from Class_Initialization import Regen_Channel
import numpy
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

init = 1

# MATERIAL PROPERTIES
rc = Regen_Channel() 
    # (self, Length, Inner Diameter, Outer Diameter, Area, Hydraulic Diameter, Relative Roughness, Friction Factor)
rc.L = 12
rc.di = 0.07091
rc.do = 0.07026355393
rc.A = ((numpy.pi / 4) * rc.do ^ 2) - ((numpy.pi / 4) * rc.di ^ 2)
rc.dh = 2 * ((rc.do/2) - (rc.di/2))