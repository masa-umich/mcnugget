import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
import numpy as np
import pint
from numpy import genfromtxt

fuel_properties = genfromtxt('rp1.csv', delimiter=',')

init = 1

class Regen_Channel:     
    L = init
    ri = init
    ro = init
    k = init
    f = init
    e = init
    sA = init
    
    def __init__(self, ro, ri):
        self.A = ((np.pi) * ro ** 2) - ((np.pi) * ri ** 2) # m^2
        self.dh = 2 * ((ro) - (ri))

class Liner:     
    k = init
    rho = init
    a = init
    v = init
    E = init
    ty = init 
    tu = init
    T = init
    sA = init

    def __init__(self, ro, ri):
        self.t = ro - ri
        self.ro = ro
        self.ri = ri

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
        self.k = np.interp(T, fuel_properties[:, 0], fuel_properties[:, 4])
        self.u = np.interp(T, fuel_properties[:, 0], fuel_properties[:, 3])
        self.cp = np.interp(T, fuel_properties[:, 0], fuel_properties[:, 1])
        self.rho = np.interp(T, fuel_properties[:, 0], fuel_properties[:, 2])






