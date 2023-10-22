# Blowdown Modelling Project
# https://www.et.byu.edu/~wheeler/Tank_Blowdown_Math.pdf
# https://en.wikipedia.org/wiki/Choked_flow
import matplotlib.pyplot as plt
import os, numpy as np
from scipy.optimize import fsolve
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
from rocketcea.cea_obj import CEA_Obj


IN_TO_M = 1/39.37
PSI_TO_PA = 6894.757
L_TO_M3 = 0.001
FT_TO_M = 1/3.281
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15
os.environ['RPPREFIX'] = r'/home/jasonyc/masa/REFPROP-cmake/build'
cea = CEA_Obj(oxName="LOX", fuelName="RP1")


class EngineModel:
    def __init__(self, D_t: float = 2.925, C_F: float = 1.351, C_star: float = 1519.4,
                  C_star_eff: float = 0.85, P_c_ideal: float = 309.5):
        # Input arguments are generally in imperial (matches ME-5 master sheet)
        # D_t: Throat diameter [in]
        # C_F: Thrust coefficient [dimensionless]
        # C_star: Characteristic velocity [m/s]
        # C_star_eff: C* efficiency (injector efficiency) [dimensionless]
        # P_c_ideal: Ideal chamber pressure [psia]
        
        # Member variables are in SI base units
        self.A_t = np.pi*((D_t/2)*(IN_TO_M))**2  # [m^2]
        self.C_F = C_F                           # [NONE]
        self.C_star = C_star                     # [m/s]
        self.C_star_eff = C_star_eff             # [NONE]
        self.P_c_ideal = P_c_ideal*PSI_TO_PA     # [Pa]
        self.P_c = P_c_ideal*PSI_TO_PA           # [Pa]
        

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
    
    def __init__(self, P_0: float, T_0: float, V_0: float, gas: str = "Nitrogen"):
        self.gas = gas
        self.P = P_0    # [Pa]
        self.T = T_0    # [K]
        # Calculate initial internal energy (J/kg) and density (kg/m^3)
        self.E = self.RP.REFPROPdll(gas,"PT","E",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.rho = self.RP.REFPROPdll(gas,"PT","D",self.MASS_BASE_SI,0,0,self.P,self.T,[1.0]).Output[0]
        self.n = self.rho*V_0  # Mass of gas, conserved [kg]
        
    def update_state(self, dV: float, new_V_ullage: float):
        self.E = self.E - self.P*dV  # dE = Q-W, work done = p*dV for small dV 
        self.rho = self.n/new_V_ullage
        self.P = self.RP.REFPROPdll(self.gas,"ED","P",self.MASS_BASE_SI,0,0,self.E,self.rho,[1.0]).Output[0]
        self.T = self.RP.REFPROPdll(self.gas,"ED","T",self.MASS_BASE_SI,0,0,self.E,self.rho,[1.0]).Output[0]
        
    
    def get_state_string(self) -> str:
        return ("[GAS STATE] P: {0:.2f} psi | T: {1:.2f} K | ".format(self.P/PSI_TO_PA, self.T) +
                "Energy: {0:.3f} kJ/kg | Density: {1:.3f} kg/m^3".format(self.E/1e3, self.rho))
        

class PropTank:
    def __init__(self, V_total: float, V_prop_0: float, rho_prop: float,
                 P_ullage_0: float, T_ullage_0: float, CdA: float):
        # V_total: total tank volume (propellant + ullage) [L]
        # V_prop_0: initial liquid propellant volume [L]
        # rho_prop: density of liquid propellant, assumed constant [kg/m^3]
        # P_ullage_0: initial ullage pressure [psi]
        # T_ullage_0: initial ullage temperature [K]
        # gas_state: GasState object describing ullage gas
        # CdA: total downstream feed system CdA [m^2]
        self.V_total = V_total*L_TO_M3
        self.V_prop = V_prop_0*L_TO_M3
        self.V_ullage = self.V_total-self.V_prop
        self.ullage_frac = self.V_ullage/self.V_total
        self.rho_prop = rho_prop
        self.gas_state = GasState(P_ullage_0*PSI_TO_PA, T_ullage_0, self.V_ullage, "Nitrogen")
        self.CdA = CdA
    
    def update_state(self, dV: float):
        # Input dV: change in liquid propellant volume [m^3]
        self.V_prop -= dV
        self.V_ullage += dV
        self.ullage_frac = self.V_ullage/self.V_total
        # TODO: Add termination condition here when P_ullage ~= ambient pressure
        self.gas_state.update_state(dV, self.V_ullage)
    
    def get_state_string(self):
        return ("[TANK] Propellant mass: {0:.2f} kg | Ullage fraction: {1:.2f}% \n\t".format(
            self.V_prop*self.rho_prop, self.ullage_frac*100) + self.gas_state.get_state_string())


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


def get_cea_c_star(of_ratio: float, pc_ideal: float):
    return FT_TO_M*cea.get_Cstar(Pc=(pc_ideal/PSI_TO_PA), MR=of_ratio)  # [m/s]

    
def system_equations(params: tuple, *constants: tuple):
    # System of equations that represent the engine. The asterisk in `constants` packs the tuple
    mdot_o, mdot_f, c_star, F_t, P_c = params
    cda_o, rho_o, P_o, cda_f, rho_f, P_f, pc_ideal, A_t, C_F, C_star_eff = constants
    eqn1 = cda_o * np.sqrt(2*rho_o*(P_o - P_c)) - mdot_o
    eqn2 = cda_f * np.sqrt(2*rho_f*(P_f - P_c)) - mdot_f
    eqn3 = (get_cea_c_star(mdot_o/mdot_f, pc_ideal) * C_star_eff) - c_star
    eqn4 = F_t/(A_t*C_F) - P_c
    eqn5 = (mdot_o+mdot_f) * c_star * C_F - F_t
    return (eqn1, eqn2, eqn3, eqn4, eqn5)
    
    
def solve(engine: EngineModel, ox_tank: PropTank, fuel_tank: PropTank):
    runtime = 1  # [s] Overall runtime of 5 seconds
    dt = 0.001   # 1 ms timestep length
    # Variables we want so solve for:
    # mdot_o: mass flow rate of oxidizer [kg/s]
    # mdot_f: mass flow rate of fuel [kg/s]
    # c_star: effective C*, as function of only O/F ratio (fixed P_c) [m/s]
    # F_t: thrust force [N]
    # P_c: chamber pressure [Pa]
    t_range = np.arange(0, runtime, dt, dtype=float)
    F_graph = [0 for _ in range(t_range.size)]
    Pc_graph = [0 for _ in range(t_range.size)]
    Cstar_graph = [0 for _ in range(t_range.size)]
    for i in range(t_range.size):
        init_guess = tuple((4, 2, 1500, 12000, 2.1e6))
        constants = tuple((ox_tank.CdA, ox_tank.rho_prop, ox_tank.gas_state.P, fuel_tank.CdA, fuel_tank.rho_prop, 
                    fuel_tank.gas_state.P, engine.P_c_ideal, engine.A_t, engine.C_F, engine.C_star_eff))
        mdot_o, mdot_f, c_star, F_t, P_c = fsolve(system_equations, init_guess, args=constants)
        # We've solved the downstream conditions, now need to update PropTank with our delta mass
        ox_dV = (mdot_o*dt)/(ox_tank.rho_prop)
        fuel_dV = (mdot_f*dt)/(fuel_tank.rho_prop)
        ox_tank.update_state(ox_dV)
        fuel_tank.update_state(fuel_dV)
        # Update data
        F_graph[i], Pc_graph[i], Cstar_graph[i] = F_t, P_c, c_star
    
    # Print final state of the system
    ox_str = ox_tank.get_state_string()
    fuel_str = fuel_tank.get_state_string()
    print("----- Final system state: -----")
    print("Oxdizer [LOX]:" + "\n\t" + ox_str)
    print("Fuel [RP-1]:" + "\n\t" + fuel_str)
    # Graph values
    fig, axs = plt.subplots(3,1)
    fig.set_size_inches((12, 8))
    fig.suptitle("ME-5 Transient Blowdown Engine Performance")
    axs[0].plot(t_range, np.array(F_graph)/1000)
    axs[1].plot(t_range, np.array(Pc_graph)/1e5)
    axs[2].plot(t_range, np.array(Cstar_graph))
    plt.xlabel("Time [s]")
    axs.flat[0].set(ylabel = "Thrust [kN]")
    axs.flat[1].set(ylabel = "Chamber pressure [barA]")
    axs.flat[2].set(ylabel = "C* (effective) [m/s]")
    plt.show()
    

if __name__ == "__main__":
    rp1_rho = 900   # Typically 810 to 1020 [kg/m^3]
    lox_rho = 1140  # At boiling point [kg/m^3]
    # Initial COPV: ~1000 psia, room temperature, 50 L
    # copv = COPV(7e6, 298, 0.05, dt)
    me_5 = EngineModel()
    # Ox tank is 80 L with 70 L of LOX at 600 psi and 200K ullage
    ox_tank = PropTank(80, 70, rp1_rho, 600, 200, 0.0001419634254)
    # Fuel tank is 30 L with 20 L of RP-1 at 500 psi and 298K ullage
    fuel_tank = PropTank(30, 20, rp1_rho, 500, 298, 0.00005878550926)
    # Print initial state of the system
    ox_str = ox_tank.get_state_string()
    fuel_str = fuel_tank.get_state_string()
    print("----- Initial system state: -----")
    print("Oxdizer [LOX]:" + "\n\t" + ox_str)
    print("Fuel [RP-1]:" + "\n\t" + fuel_str)
    solve(me_5, ox_tank, fuel_tank)
