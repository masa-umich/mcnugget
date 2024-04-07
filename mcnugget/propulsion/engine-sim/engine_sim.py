# Full burn duration engine simulator
# Generates a thrust curve as a function of time
# For a techincal walkthrough, see ./engine_sim_explained.md

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import os, yaml, csv, warnings
import constants as consts
from system_helpers import *

os.environ['RPPREFIX'] = r'/home/jasonyc/masa/REFPROP-cmake/build'


class GasState:
    """
    Static class variables for running REFPROP across all instances.
    NOTE: All internal member variables of all classes will be in base SI units.
    """
    _RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    _RP.SETPATHdll(os.environ['RPPREFIX'])
    _MASS_BASE_SI = _RP.GETENUMdll(0,"MASS BASE SI").iEnum
    @property
    def RP(self):
        return type(self)._RP
    @property
    def MASS_BASE_SI(self):
        return type(self)._MASS_BASE_SI


class COPV(GasState):
    # Models the COPV undergoing isentropic expansion
    def __init__(self, P_0: float, T_0: float, V_0: float, gas: str = "Nitrogen"):
        self.gas = gas
        self.P = P_0*consts.PSI_TO_PA
        self.T = T_0
        self.V = V_0*consts.L_TO_M3
        # Calculate initial internal energy (J/kg) and density (kg/m^3)
        self.h = self.RP.REFPROPdll(gas,"PT","H",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.rho = self.RP.REFPROPdll(gas,"PT","D",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.n = self.rho*V_0  # Mass of gas, conserved [kg]
        self.s = self.RP.REFPROPdll(gas,"PT","S",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
    
    # def update_state(self, dV: float, new_V_ullage: float):
    #     pass
    
    def get_state_string(self) -> str:
        return ("[GAS STATE] P: {0:.2f} psi | T: {1:.2f} K | ".format(self.P/consts.PSI_TO_PA, self.T) +
                "Energy: {0:.3f} kJ/kg | Density: {1:.3f} kg/m^3".format(self.E/1e3, self.rho))
 
 
class Ullage(GasState):
    def __init__(self, P_0: float, T_0: float, V_0: float, gas: str = "Nitrogen"):
        self.P = P_0
        self.T = T_0
        self.gas = gas
        # Calculate initial internal energy (J/kg) and density (kg/m^3)
        self.e = self.RP.REFPROPdll(gas,"PT","e",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.rho = self.RP.REFPROPdll(gas,"PT","D",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.cv = self.RP.REFPROPdll(gas,"PT","Cv",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.Z = self.RP.REFPROPdll(gas,"PT","Z",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.n = self.rho*V_0  # Mass of gas, conserved [kg]
        
    # def update_state(self, dV: float, new_V_ullage: float):
    #     self.E = self.E - self.P*dV  # dE = Q-W, work done = p*dV for small dV 
    #     self.rho = self.n/new_V_ullage
    #     self.P = self.RP.REFPROPdll(self.gas,"ED","P",self.MASS_BASE_SI,0,0,self.E,self.rho,[1.0]).Output[0]
    #     self.T = self.RP.REFPROPdll(self.gas,"ED","T",self.MASS_BASE_SI,0,0,self.E,self.rho,[1.0]).Output[0]
 
 
class PropTank:
    # Models a single propellant tank
    def __init__(self, rho_prop: float, V_total: float, V_prop_0: float, P_ullage_0: float, 
                 T_ullage_0: float, CdA: float, collapse_K: float = 1.0):
        # rho_prop: density of liquid propellant, assumed constant
        # V_total: total tank volume (propellant + ullage)
        # V_prop_0: initial liquid propellant volume
        # P_ullage_0: initial ullage pressure [psi]
        # T_ullage_0: initial ullage temperature [K]
        # CdA: total downstream feed system CdA [m^2]
        # collapse_K: collapse factor, ratio of ideal ullage gas inflow mass flow to real
        # gas_state: Ullage object describing ullage gas
        
        self.rho_prop = rho_prop
        self.V_total = V_total*consts.L_TO_M3
        self.V_prop = V_prop_0*consts.L_TO_M3
        self.V_ullage = self.V_total-self.V_prop
        self.ullage_frac = self.V_ullage/self.V_total
        self.CdA = CdA
        self.collapse_K = collapse_K
        self.gas_state = Ullage(P_ullage_0*consts.PSI_TO_PA, T_ullage_0, self.V_ullage)
        
    def get_update_params(self):
        # Returns needed values of the previous ullage state to solve feed system. 
        # (e, p, m, cv, T, Z)
        return (self.gas_state.e, self.gas_state.P, self.gas_state.n, self.gas_state.cv,
                self.gas_state.T, self.gas_state.Z, self.V_ullage)


class Engine:
    # Models a liquid bipropellant engine, parameters should match ME-5 master sheet
    def __init__(self, D_t: float, C_F: float, C_star: float, C_star_eff: float, 
                 P_c_ideal: float, P_a: float):
        # D_t: Throat diameter
        # C_F: Thrust coefficient (nozzle efficiency)
        # C_star: Characteristic velocity
        # C_star_eff: C* efficiency (injector efficiency)
        # P_c_ideal: Ideal chamber pressure
        # P_a: Ambient pressure (assumed constant)
        
        self.A_t = np.pi*((D_t/2)*(consts.IN_TO_M))**2  # [m^2]
        self.C_F = C_F                                  # [NONE]
        self.C_star = C_star                            # [m/s]
        self.C_star_eff = C_star_eff                    # [NONE]
        self.P_c_ideal = P_c_ideal*consts.PSI_TO_PA     # [Pa]
        self.P_c = P_c_ideal*consts.PSI_TO_PA           # [Pa]
        self.P_a = P_a                                  # [Pa]


class DataTracker():
    def __init__(self):
        self._mdot_liq_o = list()
        self._mdot_liq_f = list()
        self._c_star = list()
        self._F_t = list()
        self._P_c = list()
        
    def update_engine_data(self, mdot_o, mdot_f, c_star, F_t, P_c):
        self._mdot_liq_o.append(mdot_o)
        self._mdot_liq_f.append(mdot_f)
        self._c_star.append(c_star)
        self._F_t.append(F_t)
        self._P_c.append(P_c)
        
    def print_data(self):
        print("Printing engine data:")
        print(self._c_star)
        print(self._F_t)
        print([x/consts.PSI_TO_PA for x in self._P_c])
        

def solve_engine(lox_tank: PropTank, fuel_tank: PropTank, engine: Engine, tracker: DataTracker):
    """
    Return the liquid volumetric flow rate for fuel and ox, and store simulation data to 
    a DataTracker for storage and plotting.
    """
    init_guess = tuple((8, 4, 1500, 12500, 2.1e6))
    # TODO: Update the init_guess with something more reasonable from the previous state
    const_params = tuple((lox_tank.CdA, lox_tank.rho_prop, lox_tank.gas_state.P, fuel_tank.CdA, 
                       fuel_tank.rho_prop, fuel_tank.gas_state.P, engine.P_c_ideal, 
                       engine.A_t, engine.C_F, engine.C_star_eff))
    results = fsolve(tca_system_eqns, init_guess, args=const_params)
    tracker.update_engine_data(*results)
    # Returns liquid mdot_o and mdot_f
    return results[0], results[1]
    
    
def solve_feed(lox_tank: PropTank, fuel_tank: PropTank, copv: COPV,
               tracker: DataTracker, liquid_mdots: tuple, dt: float, reg_cda: float):
    """
    Return the new ullage state variables (namely E, p, T) to perform a lox_tank and fuel_tank
    update. Also return gas mass flow rates to update COPV state. This function will solve 
    a different system of equations based on if the dome regulator is choked. 
    """
    # First, the LOX tank parameters
    mdot_liq_o, mdot_liq_f = liquid_mdots
    init_guess = tuple((90e3, 250, 3.4e6, 0.4, 5e-3))
    const_params = tuple((*lox_tank.get_update_params(), copv.P, copv.h, 
                          mdot_liq_o/consts.LOX_RHO, dt))
    # Unknowns in order are: [E, T, p, m, mdot]
    results = fsolve(feed_system_eqns, init_guess, args=const_params)
    print("Initial LOX values:")
    print(f"E: {lox_tank.gas_state.e*lox_tank.gas_state.n/1000:.2f} kJ | T: {lox_tank.gas_state.T:.2f} K",
          f"| p: {lox_tank.gas_state.P/consts.PSI_TO_PA:.2f} psi | m: {lox_tank.gas_state.n:.3f} kg")
    print("Next LOX values:")
    print(f"E: {results[0]/1000:.2f} kJ | T: {results[1]:.2f} K | p: {results[2]/consts.PSI_TO_PA:.2f} psi ",
          f"| m: {results[3]:.3f} kg | mdot: {(results[4]):.3f} kg/s")
    # Next, the fuel tank
    init_guess = tuple((90e3, 250, 3.4e6, 0.4, 5e-3))
    const_params = tuple((*fuel_tank.get_update_params(), copv.P, copv.h, 
                          mdot_liq_f/consts.RP1_RHO, dt))
    results = fsolve(feed_system_eqns, init_guess, args=const_params)
    print("Initial fuel values:")
    print(f"E: {fuel_tank.gas_state.e*fuel_tank.gas_state.n/1000:.2f} kJ | T: {fuel_tank.gas_state.T:.2f} K",
          f"| p: {fuel_tank.gas_state.P/consts.PSI_TO_PA:.2f} psi | m: {fuel_tank.gas_state.n:.3f} kg")
    print("Next fuel values:")
    print(f"E: {results[0]/1000:.2f} kJ | T: {results[1]:.2f} K | p: {results[2]/consts.PSI_TO_PA:.2f} psi ",
          f"| m: {results[3]:.3f} kg | mdot: {(results[4]):.3f} kg/s")
    


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    # Load input parameters from YAML file
    with open("input.yaml", "r") as file:
        params = yaml.safe_load(file)
    
    copv = COPV(*list(params["copv"].values()))
    lox_tank = PropTank(*([consts.LOX_RHO] + list(params["lox_tank"].values())))
    fuel_tank = PropTank(*([consts.RP1_RHO] + list(params["fuel_tank"].values())))
    engine = Engine(*list(params["engine"].values()))
    tracker = DataTracker()
    
    # First, solve engine system using current ullage pressure
    liquid_mdots = solve_engine(lox_tank, fuel_tank, engine, tracker)
    tracker.print_data()
    # Next, solve feed system
    controlled_regime = True
    dt = float(params["dt"])
    reg_cda = float(params["dt"])
    solve_feed(lox_tank, fuel_tank, copv, tracker, liquid_mdots, dt, reg_cda)
    