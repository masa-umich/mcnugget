# Full burn duration engine simulator
# Generates a thrust curve as a function of time
# For a techincal walkthrough, see ./engine_sim_explained.md

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import os, yaml, csv
import constants as consts
from tca_helpers import tca_system_eqns


def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15
def scfm_to_mdot(scfm): return ((scfm/60)*consts.GN2_RHO_IMP)*consts.LBM_TO_KG
def mdot_to_scfm(mdot): return ((mdot/consts.LBM_TO_KG)/consts.GN2_RHO_IMP)*60
os.environ['RPPREFIX'] = r'/home/jasonyc/masa/REFPROP-cmake/build'


def get_reg_outlet(inlet_p: float, mdot: float) -> float:
    """
    Return the outlet pressure of the dome regulator given a mass flow and inlet pressure.
    These explicit functions are data interpolations from our regulator manufacturer Premier,
    which gave several inlet pressure curves (ksi) as a function of SCFM and outlet [psig].
    Args:
        inlet_p: Inlet pressure [Pa]
        mdot: Mass flow requirement [kg/s]
    Returns:
        float: Outlet pressure [Pa]
    General form of our function: a*tan(-x/b)+475
    The coefficient a has a range of [5,35] (linear relation with inlet pressure)
    The coefficient b has a range of [750, 1310] (exponential relation with inlet pressure)
    Example: 35*tan(-x/750)+475 is for the 1 ksi inlet pressure
    Example: 25*tan(-x/830)+475 is for the 1.5 ksi inlet pressure
    Note: Given 4.5 ksi and room temp, max choked mdot of a 1" ID pipe is ~36 kg/s, and 
    500 psi + 1" ID is ~4 kg/s (7200 SCFM). Thus, we will lose control of the dome regulator
    far before pipe choking becomes an issue, i.e. 850 SCFM (0.467 kg/s) is the upper limit.
    """
    scfm_val = mdot_to_scfm(mdot)
    assert(scfm_val < 850 and scfm_val > 0)
    coeff_a = 0
    raise NotImplementedError
    # As the reg increases its flow area, the demand for mass flow to bring the exit pressure
    # increases at a faster rate than it can increase the flow area. So eventually the 
    # pressure ratio keeps increasing (even as mdot increases) until it reaches the critical
    # pressure ratio, at which it chokes and we have achieved the max mdot of the system.
    # This is where we switch to a choked flow model of the system until the COPV pressure
    # is basically the ullage pressure, after which we can switch to a blowdown model.
    # Additionally, the reason we can just plug in our dome reg curve into the system of
    # equations is because the "tendancy" to go towards the set pressure of ~500 psi is built
    # into the curve itself; initially the ullage is at 500 psi anyway, and as we only lower
    # ullage pressure marginally (e.g. to 490 psi), we get very low SCFM needed to try 
    # getting back to 500 psi, even though the actual downstream pressure is lower than set.
    # Google "swagelok" and "pressure droop" and "lockup" to learn more about reg curves.


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
        self.e = self.RP.REFPROPdll(gas,"PT","E",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.rho = self.RP.REFPROPdll(gas,"PT","D",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.n = self.rho*V_0  # Mass of gas, conserved [kg]
        self.s = self.RP.REFPROPdll(gas,"PT","S",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
    
    def update_state(self, dV: float, new_V_ullage: float):
        pass
    
    def get_h(self) -> float:
        # Get the specific enthalpy of the COPV gas
        return self.RP.REFPROPdll(gas,"PT","H",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
    
    def get_state_string(self) -> str:
        return ("[GAS STATE] P: {0:.2f} psi | T: {1:.2f} K | ".format(self.P/consts.PSI_TO_PA, self.T) +
                "Energy: {0:.3f} kJ/kg | Density: {1:.3f} kg/m^3".format(self.E/1e3, self.rho))
 
 
class Ullage(GasState):
    def __init__(self, P_0: float, T_0: float, V_0: float, gas: str = "Nitrogen"):
        self.P = P_0
        self.T = T_0
        self.gas = gas
        # Calculate initial internal energy (J/kg) and density (kg/m^3)
        self.E = self.RP.REFPROPdll(gas,"PT","E",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.rho = self.RP.REFPROPdll(gas,"PT","D",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.n = self.rho*V_0  # Mass of gas, conserved [kg]
        
    def update_state(self, dV: float, new_V_ullage: float):
        self.E = self.E - self.P*dV  # dE = Q-W, work done = p*dV for small dV 
        self.rho = self.n/new_V_ullage
        self.P = self.RP.REFPROPdll(self.gas,"ED","P",self.MASS_BASE_SI,0,0,self.E,self.rho,[1.0]).Output[0]
        self.T = self.RP.REFPROPdll(self.gas,"ED","T",self.MASS_BASE_SI,0,0,self.E,self.rho,[1.0]).Output[0]
 
 
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
        print(self._c_star)
        print(self._F_t)
        print([x/consts.PSI_TO_PA for x in self._P_c])
        


def solve_engine(lox_tank: PropTank, fuel_tank: PropTank, engine: Engine, tracker: DataTracker):
    """
    Return the liquid volumetric flow rate for fuel and ox, and store simulation data to 
    a DataTracker for storage and plotting.
    """
    init_guess = tuple((8, 4, 1500, 12500, 2.1e6))
    const_params = tuple((lox_tank.CdA, lox_tank.rho_prop, lox_tank.gas_state.P, fuel_tank.CdA, 
                       fuel_tank.rho_prop, fuel_tank.gas_state.P, engine.P_c_ideal, 
                       engine.A_t, engine.C_F, engine.C_star_eff))
    results = fsolve(tca_system_eqns, init_guess, args=const_params)
    tracker.update_engine_data(*results)
    # Returns liquid mdot_o and mdot_f
    return results[0], results[1]
    
    
def solve_feed(lox_tank: PropTank, fuel_tank: PropTank, engine: Engine, copv: COPV,
               tracker: DataTracker, liquid_mdots: tuple, controlled: bool):
    """
    Return the new ullage state variables (namely E, p, T) to perform a lox_tank and fuel_tank
    update. Also return gas mass flow rates to update COPV state. This function will solve 
    a different system of equations based on if the dome regulator is choked. 
    """
    # First, the LOX tank parameters
    mdot_liq_o, mdot_liq_f = liquid_mdots
    const_params = tuple((lox_tank, copv.get_h(), mdot_liq_o/consts.LOX_RHO))
    


if __name__ == "__main__":
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
    
    