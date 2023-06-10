import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
import numpy as np
import pint
from numpy import genfromtxt

fuel_properties = genfromtxt('rp1.csv', delimiter=',')

init = 1

class Regen_Channel:     
    L = init
    di = init
    do = init
    A = init
    dh = init
    k = init
    f = init

class Liner:     
    k = init
    rho = init
    a = init
    v = init
    E = init
    ty = init 
    tu = init
    di = init
    do = init
    T = init

# Interopolates Fuel Properties at a given temperature
# Inputs: Temperature (K)
# Outputs: conductivity, viscosity, Prandtl Number, Specific Heat, Density

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






