# Full burn duration engine simulator
# Generates a thrust curve as a function of time
# For a techincal walkthrough, see ./engine_sim_explained.md

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve, least_squares
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import os, yaml, warnings
import constants as consts
from system_helpers import *
from DataTracker import *

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
        self.h = self.RP.REFPROPdll(gas,"PT","h",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.rho = self.RP.REFPROPdll(gas,"PT","D",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.n = self.rho*self.V  # Mass of gas, conserved [kg]
        self.s = self.RP.REFPROPdll(gas,"PT","S",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
    
    def update_state(self, delta_mass: float):
        self.n += delta_mass
        self.rho = self.n/self.V
        self.s = self.s
        
        self.P = self.RP.REFPROPdll(self.gas,"DS","P",self.MASS_BASE_SI,0,0,self.rho,self.s,[1.0]).Output[0]
        self.T = self.RP.REFPROPdll(self.gas,"DS","T",self.MASS_BASE_SI,0,0,self.rho,self.s,[1.0]).Output[0]
        self.h = self.RP.REFPROPdll(self.gas,"DS","h",self.MASS_BASE_SI,0,0,self.rho,self.s,[1.0]).Output[0]
    
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
        
    def update(self, P_new: float, n_new: float, V_ullage_new: float):
        self.P = P_new
        self.n = n_new
        self.rho = self.n/V_ullage_new
        
        self.T = self.RP.REFPROPdll(self.gas,"PD","T",self.MASS_BASE_SI,0,0,self.P,self.rho,[1.0]).Output[0]
        self.e = self.RP.REFPROPdll(self.gas,"PD","e",self.MASS_BASE_SI,0,0,self.P,self.rho,[1.0]).Output[0]
        self.cv = self.RP.REFPROPdll(self.gas,"PD","Cv",self.MASS_BASE_SI,0,0,self.P,self.rho,[1.0]).Output[0]
        self.Z = self.RP.REFPROPdll(self.gas,"PD","Z",self.MASS_BASE_SI,0,0,self.P,self.rho,[1.0]).Output[0]
 

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
        # ullage: Ullage object describing ullage gas
        self.rho_prop = rho_prop
        self.V_total = V_total*consts.L_TO_M3
        self.V_prop = V_prop_0*consts.L_TO_M3
        self.V_ullage = self.V_total-self.V_prop
        self.ullage_frac = self.V_ullage/self.V_total
        self.CdA = CdA
        self.collapse_K = collapse_K
        self.ullage = Ullage(P_ullage_0*consts.PSI_TO_PA, T_ullage_0, self.V_ullage)
        
    def get_update_params(self):
        # Returns needed values of the previous ullage state to solve feed system.
        return (self.ullage.e, self.ullage.P, self.ullage.n, self.ullage.cv,
                self.ullage.T, self.ullage.Z, self.V_ullage)
        
    def update_state(self, results: list):
        # [E, T, p, m, mdot, dV_liquid]
        assert(len(results) == 6)
        self.V_prop -= results[-1]
        self.V_ullage += results[-1]
        self.ullage_frac = self.V_ullage/self.V_total
        self.ullage.update(results[2], results[3], self.V_ullage)


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


def solve_engine(lox_tank: PropTank, fuel_tank: PropTank, engine: Engine, tracker: DataTracker):
    """
    Return the liquid volumetric flow rate for fuel and ox, and store simulation data to 
    a DataTracker for storage and plotting.
    """
    # Unknowns in order are: [mdot_liq_ox, mdot_liq_fuel, C_star, F_t, P_c]
    init_guess = tuple((8, 4, 1500, 12500, 2.1e6))
    # TODO: Update the init_guess with something more reasonable from the previous state
    const_params = tuple((lox_tank.CdA, lox_tank.rho_prop, lox_tank.ullage.P, fuel_tank.CdA, 
                       fuel_tank.rho_prop, fuel_tank.ullage.P, engine.P_c_ideal, 
                       engine.A_t, engine.C_F, engine.C_star_eff))
    results = fsolve(tca_system_eqns, init_guess, args=const_params)
    tracker.update_engine_data(*results, engine.C_F)
    # Returns liquid mdot_o and mdot_f
    return results[0], results[1]
    
    
def solve_feed(lox_tank: PropTank, fuel_tank: PropTank, copv: COPV, tracker: DataTracker,
               liquid_mdots: tuple, dt: float, step: int):
    """
    Return the new ullage state variables (namely E, p, T) to perform a lox_tank and fuel_tank
    update. Also return gas mass flow rates to update COPV state. This function will solve 
    a different system of equations based on if the dome regulator is choked. 
    """
    # First, the LOX tank parameters
    mdot_liq_o, mdot_liq_f = liquid_mdots
    init_guess = tuple((90e3, 250, 3.4e6, 0.4, 0.1))
    const_params = tuple((*lox_tank.get_update_params(), copv.P, copv.h, 
                          mdot_liq_o/consts.LOX_RHO, dt, lox_tank.collapse_K))
    # Unknowns in order are: [E, T, p, m, mdot]
    limit = 1e20
    soln_bounds = ((0, 0, 0, 0, 0), (limit, 4e3, limit, limit, limit))
    ox_results = least_squares(feed_system_eqns, init_guess, args=const_params, bounds=soln_bounds).x
    # Next, the fuel tank
    init_guess = tuple((30e3, 250, 3.4e6, 0.2, 0.1))
    const_params = tuple((*fuel_tank.get_update_params(), copv.P, copv.h, 
                          mdot_liq_f/consts.RP1_RHO, dt, fuel_tank.collapse_K))
    fuel_results = least_squares(feed_system_eqns, init_guess, args=const_params, bounds=soln_bounds).x
    print(f"[Time: {dt*step:.2f} s] <LOX> [E: {ox_results[0]/1000:.0f} kJ, T: {ox_results[1]:.0f} " +
          f"K, p: {ox_results[2]/consts.PSI_TO_PA:.2f} psi, " +
          f"mdot: {(ox_results[4]):.3f} kg/s]" +
          f" <FUEL> [E: {fuel_results[0]/1000:.0f} kJ, T: {fuel_results[1]:.0f} K, p: " +
          f"{fuel_results[2]/consts.PSI_TO_PA:.2f} psi, " +
          f"mdot: {(fuel_results[4]):.3f} kg/s]")
    return ox_results, fuel_results


def update_states(lox_tank: PropTank, fuel_tank: PropTank, copv: COPV, tracker: DataTracker, 
                  feed_results: tuple, liquid_mdots: tuple, dt: float):
    # Update both ullage and COPV states with the feed system solution from the previous timestep
    ox_results, fuel_results = feed_results
    ox_results = list(ox_results) + [liquid_mdots[0]/consts.LOX_RHO*dt]
    fuel_results = list(fuel_results) + [liquid_mdots[1]/consts.RP1_RHO*dt]
    # [E, T, p, m, mdot, dV_liquid]
    lox_tank.update_state(ox_results)
    fuel_tank.update_state(fuel_results)
    # Now, update the COPV state
    copv_gas_mass_delta = -1 * (ox_results[4]*dt + fuel_results[4]*dt)
    copv.update_state(copv_gas_mass_delta)
    # Prepare data for export to the DataTracker: [P_ullage, T_ullage, V_prop, mdot_ullage]
    lox_info = [lox_tank.ullage.P, lox_tank.ullage.T, lox_tank.V_prop, ox_results[4]]
    fuel_info = [fuel_tank.ullage.P, fuel_tank.ullage.T, fuel_tank.V_prop, fuel_results[4]]
    tracker.update_feed_data(copv.P, lox_info, fuel_info)


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
    
    runtime = float(params["runtime"])
    dt = float(params["dt"])
    for step in range(0, int(np.ceil(runtime/dt))):
        # First, solve engine system using current ullage pressure
        liquid_mdots = solve_engine(lox_tank, fuel_tank, engine, tracker)
        # Next, solve feed system
        controlled_regime = True
        feed_results = solve_feed(lox_tank, fuel_tank, copv, tracker, liquid_mdots, dt, step)
        update_states(lox_tank, fuel_tank, copv, tracker, feed_results, liquid_mdots, dt)
        tracker.update_counters(dt, step)
        if (tracker._fuel_liq_v[-1] < 0.1 or tracker._ox_liq_v[-1] < 0.1):
            print("Simulation terminated early: propellant depleted")
            break
        
    # Plot the data recorded in tracker
    tracker.plot_data()
    print(tracker.get_end_string())
    if (bool(params["save_csv"])):
        tracker.export_thrust_curve()
    plt.show()
