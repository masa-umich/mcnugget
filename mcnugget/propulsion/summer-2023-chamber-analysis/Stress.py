import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
from class_init import Regen_Channel
from class_init import Liner
from class_init import Fuel
import numpy as np

# Function that Calculates the Maximum Radial Stress on the Liner
# Inputs: Liner Material Properties, Hotwall Temperature, Coldwall Temperature, Coolant Pressure, Chamber Presure, Liner Inner Diameter
# Returns Maximum Compressive Stress


def radial_stress(q, r_o, r_i, P_c, P_f, E, a, k, v):
    return (((P_f - P_c) * (r_i)) / (r_o - r_i)) + (E * a * q * (r_o - r_i)) / (
        2 * (1 - v) * k
    )


# Function that Calculates Constrained Thermal Expansion Stress
# Inputs: Liner Material Properties, Axial Temperature Gradient
# Returns the Axial Compressive Stress


def axial_stress(E, a, dT, v):
    return (E * a * dT) / (2 * (1 - v))


# Function that Calculates the Von Mises Stress
# Inputs: Principal Stresses
# Returns the Von Mises Stress
def von_mises(sigma1, sigma2):
    return np.sqrt((sigma1**2) + (sigma2**2) - (sigma1 * sigma2))
