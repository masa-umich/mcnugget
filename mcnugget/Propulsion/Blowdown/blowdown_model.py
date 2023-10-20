# Blowdown Modelling Project
# https://www.et.byu.edu/~wheeler/Tank_Blowdown_Math.pdf
# https://en.wikipedia.org/wiki/Choked_flow
import matplotlib.pyplot as plt
import os, numpy as np
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary


IN_TO_M = 1/39.37
PSI_TO_PA = 6894.757
L_TO_M3 = 0.001
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15
os.environ['RPPREFIX'] = r'/home/jasonyc/masa/REFPROP-cmake/build'


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
        

class GasState:
    # Static class variables for running REFPROP across all instances
    _RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    _RP.SETPATHdll(os.environ['RPPREFIX'])
    _MASS_BASE_SI = _RP.GETENUMdll(0,"MASS BASE SI").iEnum
    
    @property
    def RP(self):
        return type(self)._RP
    
    @property
    def MASS_BASE_SI(self):
        return type(self)._MASS_BASE_SI
    
    def __init__(self, P_0: float, T_0: float, gas: str = "Nitrogen"):
        self.gas = gas
        self.P = P_0    # [Pa]
        self.T = T_0    # [K]
        # Calculate initial internal energy (J/kg) and density (kg/m^3)
        self.E = self.RP.REFPROPdll(gas,"PT","E",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.rho = self.RP.REFPROPdll(gas,"PT","D",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        
    def print_state(self):
        print("[GAS STATE] P: {0:.2f} psi | T: {1:.2f} K | ".format(self.P/PSI_TO_PA, self.T) +
              "Energy: {0:.3f} kJ/kg | Density: {1:.3f} kg/m^3".format(self.E/1e3, self.rho))
        

class PropTank:
    def __init__(self, V_total: float, V_prop_0: float, rho_prop: float,
                 P_ullage_0: float, T_ullage_0: float):
        # V_total: total tank volume (propellant + ullage) [L]
        # V_prop_0: initial liquid propellant volume [L]
        # rho_prop: density of liquid propellant, assumed constant [kg/m^3]
        # P_ullage_0: initial ullage pressure [psi]
        # T_ullage_0: initial ullage temperature [K]
        # gas_state: GasState object describing ullage gas
        self.V_total = V_total*L_TO_M3
        self.V_prop = V_prop_0*L_TO_M3
        self.V_ullage = V_total-V_prop_0
        self.ullage_frac = self.V_ullage/self.V_total
        self.rho_prop = rho_prop
        self.gas_state = GasState(P_ullage_0*PSI_TO_PA, T_ullage_0, "Nitrogen")
    
    def update_state(self):
        pass
    
    def print_state(self):
        self.gas_state.print_state()


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
        # TODO: Get gas properties from CoolProp or pyfluids
        # c_o = np.sqrt((gamma*R*T_o)/M)
        # Discharge time constant
        # tau = (V_tank/(Cd*A_star*c_o))*(((gamma+1)/2)^((gamma+1)/(2*gamma - 2)))
        # Adiabatic tank P, V, rho
        # P_tank = P_o*((1 + ((gamma - 1)/2)*(t/tau))^(2/(1-gamma)))
        # rho_tank = rho_o*((1 + ((gamma - 1)/2)*(t/tau))^(2*gamma/(1-gamma)))
        # T_tank = T_o*((1 + ((gamma - 1)/2)*(t/tau))^(2/(1-gamma)))
        self.current_t += self.dt
        
    
class SystemState:
    def __init__(self):
        raise NotImplementedError
        
        
def solve():
    runtime = 30  # [s] Overall runtime of 30 seconds
    dt = 0.001  # 1 ms timestep length
    # Initial COPV: ~1000 psia, room temperature, 50 L
    # copv = COPV(7e6, 298, 0.05, dt)
    me_5 = EngineSpecs()
    rp1_rho = 900   # Typically 810 to 1020 [kg/m^3]
    lox_rho = 1140  # At boiling point [kg/m^3]
    # Fuel tank is 30 L with 20 L of RP-1 at 500 psi and 298K ullage
    fuel_tank = PropTank(30, 20, rp1_rho, 500, 298)
    # Ox tank is 80 L with 70 L of LOX at 600 psi and 200K ullage
    ox_tank = PropTank(80, 70, rp1_rho, 600, 200)
    fuel_tank.print_state()
    ox_tank.print_state()
    
        
if __name__ == "__main__":
    solve()
