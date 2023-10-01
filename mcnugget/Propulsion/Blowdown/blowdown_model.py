# Blowdown Modelling Project

import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
from pyfluids import Fluid, FluidsList, Input


IN_TO_M = 1/39.37
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15

class EngineSpecs:
    def __init__(self, D_t: float = 2.925, C_F: float = 1.351, 
                 C_star: float = 1519.4, P_c_ideal: float = 309.5):
        # Input D_t is throat diameter in inches
        self.A_t = np.pi*((D_t/2)*(IN_TO_M))**2  # [m^2] Area of throat
        self.C_F = C_F
        self.C_star = C_star  # [m/s] Characteristic velocity
        self.P_c_idea = P_c_ideal  # Ideal 
        

class COPV:
    def __init__(self, P_0, rho_0, T_0, dt: float):
        self.P_0 = P_0 
        self.rho_0 = rho_0
        self.T_0 = T_0
        self.current_t = 0
        self.dt = dt
        
        
    def increment_dt():
        t = self.current_t
        
        # TODO: Get gas properties from CoolProp or pyfluids
        # c_o = np.sqrt((gamma*R*T_o)/M)
        #Discharge time constant
        # tau = (V_tank/(Cd*A_star*c_o))*(((gamma+1)/2)^((gamma+1)/(2*gamma - 2)))
        #Adiabatic tank P, V, rho
        # P_tank = P_o*((1 + ((gamma - 1)/2)*(t/tau))^(2/(1-gamma)))
        # rho_tank = rho_o*((1 + ((gamma - 1)/2)*(t/tau))^(2*gamma/(1-gamma)))
        # T_tank = T_o*((1 + ((gamma - 1)/2)*(t/tau))^(2/(1-gamma)))
        
        self.current_t += self.dt
        
    

class SystemState:
    def __init__(self):
        raise NotImplementedError
        
        
def solve(eng: EngineSpecs):
    runtime = 30  # [s] Overall runtime of 30 seconds
    dt = runtime/1e4  # [s] Time step size 
    
    
def get_new_COPV_state(copv: COPV):
    pass
    
        
if __name__ == "__main__":
    me_5 = EngineSpecs()
    solve(me_5)
