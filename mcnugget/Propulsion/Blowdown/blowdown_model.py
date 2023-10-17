# Blowdown Modelling Project
# https://www.et.byu.edu/~wheeler/Tank_Blowdown_Math.pdf
# https://en.wikipedia.org/wiki/Choked_flow
import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
from pyfluids import Fluid, FluidsList, Input


IN_TO_M = 1/39.37
PSI_TO_PA = 6894.757
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15

class EngineSpecs:
    def __init__(self, D_t: float = 2.925, C_F: float = 1.351, 
                 C_star: float = 1519.4, P_c_ideal: float = 309.5):
        # Input arguments are generally in imperial (matches ME-5 master sheet)
        # D_t: Throat diameter [in]
        # C_F: Thrust coefficient [dimensionless]
        # C_star: Characteristic velocity [m/s]
        # P_c_ideal: Ideal chamber pressure [psia]
        
        # Member variables are in SI base units
        self.A_t = np.pi*((D_t/2)*(IN_TO_M))**2  # [m^2]
        self.C_F = C_F                           # [NONE]
        self.C_star = C_star                     # [m/s]
        self.P_c_ideal = P_c_ideal*PSI_TO_PA     # [Pa]
        

class COPV:
    def __init__(self, P_0: float, T_0: float, V: float, dt: float):
        # Models the COPV according to adiabatic blowdown. All units in base SI.
        # P_0: Initial pressure [Pa]
        # T_0: Initial temperature [K]
        # V: Total volume of COPV (fixed) [m^3]
        # dt: Timestep length [s]
        self.P = P_0 
        self.T = T_0
        self.V = V
        self.rho = CP.PropsSI("D", "T", self.T, "P", self.P, "Nitrogen")
        # Instantiate an AbstractState object, using the Helmholtz Equations of State backend
        # Can replace "HEOS" argument with "REFPROP" if we want to use REFPROP backend
        self.gas_state = CP.AbstractState("HEOS", "Nitrogen")  
        self.gas_state.update(CP.PT_INPUTS, self.P, self.T)
        self.dt = dt
        self.current_t = 0
        
        
    def increment_dt():
        t = self.current_t
        # tau is the discharge time constant
        # tau
        
        
        # TODO: Get gas properties from CoolProp or pyfluids
        # c_o = np.sqrt((gamma*R*T_o)/M)
        #Discharge time constant
        # tau = (V_tank/(Cd*A_star*c_o))*(((gamma+1)/2)^((gamma+1)/(2*gamma - 2)))
        #Adiabatic tank P, V, rho
        # P_tank = P_o*((1 + ((gamma - 1)/2)*(t/tau))^(2/(1-gamma)))
        # rho_tank = rho_o*((1 + ((gamma - 1)/2)*(t/tau))^(2*gamma/(1-gamma)))
        # T_tank = T_o*((1 + ((gamma - 1)/2)*(t/tau))^(2/(1-gamma)))
        
        self.current_t += self.dt
        CP.AbstractState.cpmass()
        
    


class SystemState:
    def __init__(self):
        raise NotImplementedError
        
        
def solve(eng: EngineSpecs):
    runtime = 30  # [s] Overall runtime of 30 seconds
    dt = runtime/1e4  # [s] Time step size 
    
        
if __name__ == "__main__":
    dt = 0.001  # 1 ms timestep length
    me_5 = EngineSpecs()
    # Initial COPV: ~1000 psia, room temperature, 50 L
    copv = COPV(7e6, 298, 0.05, dt)
    solve(me_5)
