import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
from class_init import fuel
from numpy import genfromtxt
import numpy as np
import pint
import pandas as pd

fuel_properties = genfromtxt('rp1.csv', delimiter=',')
print(fuel)

def fuel_prop(T):
# Interopolates Fuel Properties at a given temperature
# Inputs: Temperature (K)
# Outputs: Density (kg/m^3), Viscosity (Pa*s), Specific Heat (J/kg*K), Thermal Conductivity (W/m*K), Prandtl Number (-)
    fuel.cp = np.interp(T, fuel_properties[:,0], fuel_properties[:,1])
    fuel.rho = np.interp(T, fuel_properties[:,0], fuel_properties[:,2])
    fuel.u = np.interp(T, fuel_properties[:,0], fuel_properties[:,3])
    fuel.k = np.interp(T, fuel_properties[:,0], fuel_properties[:,4])

