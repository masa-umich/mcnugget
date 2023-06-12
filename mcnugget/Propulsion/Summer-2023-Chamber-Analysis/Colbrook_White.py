import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
from class_init import Fuel
import numpy as np

# Function that Calculates the Friction Factor using the Colbrook-White Equation
# Inputs: Reynolds Number, Relative Roughness, Hydraulic Diameter
# Returns Friction Factor

# - eps: Convvergence Criteria
Eps = 0.001

# Function that checks if the Colbrook-White Equation has converged
def Conv_Check(f, Re, k):
    return (1 / np.sqrt(f)) + (2 * np.log10((k / 3.7) + (2.51 / (Re * np.sqrt(f)))))

# Function that calculates the Friction Factor using the Colbrook-White Equation
def Friction_Factor(Re, k):
    a = 0.01
    b = 0.04
    c = (a + b) / 2
    while (np.abs(Conv_Check(c, Re, k)) > Eps):
        if Conv_Check(c, Re, k) > 0 and Conv_Check(a, Re, k) > 0: a = c
        else: b = c
        c = (a + b) / 2
    return c