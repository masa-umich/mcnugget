# Blowdown Modelling Project

import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
from pyfluids import Fluid, FluidsList, Input


class EngineSpecs:
    def __init__(self, D_t: float = 2.925, C_F: float = 1.351, 
                 C_star: float = 1519.4, P_c_ideal: float = 309.5):
        # Input D_t is throat diameter in inches
        self.A_t = np.pi*((D_t/2)*(IN_TO_M))**2  # [m^2] Area of throat
        self.C_F = C_F
        self.C_star = C_star  # [m/s] Characteristic velocity
        self.P_c_idea = P_c_ideal  # Ideal 
        
        
def solve(eng: EngineSpecs):
    runtime = 30  # [s] Overall runtime of 30 seconds
    dt = runtime/1e4  # [s] Time step size
    
    
    
        
if __name__ == "__main__":
    me_5 = EngineSpecs()
    solve(me_5)
