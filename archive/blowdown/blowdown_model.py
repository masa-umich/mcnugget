# Blowdown Modelling Project
# https://www.et.byu.edu/~wheeler/Tank_Blowdown_Math.pdf
# https://en.wikipedia.org/wiki/Choked_flow
import matplotlib.pyplot as plt
import os, numpy as np
from scipy.optimize import fsolve
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
from rocketcea.cea_obj import CEA_Obj
import warnings
import csv


IN_TO_M = 1/39.37
PSI_TO_PA = 6894.757
L_TO_M3 = 0.001
FT_TO_M = 1/3.281
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15
os.environ['RPPREFIX'] = r'/home/jasonyc/masa/REFPROP-cmake/build'
cea = CEA_Obj(oxName="LOX", fuelName="RP1")


class EngineModel:
    def __init__(self, D_t: float = 2.925, C_F: float = 1.351, C_star: float = 1519.4,
                  C_star_eff: float = 0.85, P_c_ideal: float = 309.5, P_a: float = 1e5):
        # Input arguments are generally in imperial (matches ME-5 master sheet)
        # D_t: Throat diameter [in]
        # C_F: Thrust coefficient [dimensionless]
        # C_star: Characteristic velocity [m/s]
        # C_star_eff: C* efficiency (injector efficiency) [dimensionless]
        # P_c_ideal: Ideal chamber pressure [psia]
        # P_a: Ambient pressure (assumed constant) [Pa]
        
        # Member variables are in SI base units
        self.A_t = np.pi*((D_t/2)*(IN_TO_M))**2  # [m^2]
        self.C_F = C_F                           # [NONE]
        self.C_star = C_star                     # [m/s]
        self.C_star_eff = C_star_eff             # [NONE]
        self.P_c_ideal = P_c_ideal*PSI_TO_PA     # [Pa]
        self.P_c = P_c_ideal*PSI_TO_PA           # [Pa]
        self.P_a = P_a                           # [Pa]
        

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


def choked_flow_violated(P_c: float, of_ratio: float, P_a: float, ER: float = 10.5) -> bool: 
    # Returns true if choked flow no longer occurs at throat (engine burn is complete)
    # Expansion ratio for ME-5 of 10.5 is hard-coded here
    _, gamma = cea.get_Throat_MolWt_gamma(Pc=(P_c/PSI_TO_PA), MR=of_ratio, eps=ER, frozen=0)
    return P_c < (P_a / ((2/(gamma+1))**(gamma/(gamma-1))))


def tanks_empty(ox_tank: PropTank, fuel_tank: PropTank) -> bool:
    # Returns true if either tank has expelled all of its propellant 
    limit = 0.0005  # 0.5 L left of propellant
    return (ox_tank.V_prop < limit) or (fuel_tank.V_prop < limit)
    

    
def system_equations(params: tuple, *constants: tuple):
    # System of equations that represent the engine. The asterisk in `constants` packs the tuple
    mdot_o, mdot_f, c_star, F_t, P_c = params
    cda_o, rho_o, P_o, cda_f, rho_f, P_f, pc_ideal, A_t, C_F, C_star_eff = constants
    # eqn1 = cda_o * np.sqrt(2*rho_o*(P_o - P_c)) - mdot_o
    # eqn2 = cda_f * np.sqrt(2*rho_f*(P_f - P_c)) - mdot_f
    eqn1 = cda_o**2 * (2*rho_o*(P_o - P_c)) - mdot_o**2  # Squaring the CdA equation to avoid sqrt()
    eqn2 = cda_f**2 * (2*rho_f*(P_f - P_c)) - mdot_f**2  # Squaring the CdA equation to avoid sqrt()
    eqn3 = (get_cea_c_star(mdot_o/mdot_f, pc_ideal) * C_star_eff) - c_star
    eqn4 = F_t/(A_t*C_F) - P_
    eqn5 = (mdot_o+mdot_f) * c_star * C_F - F_t
    return (eqn1, eqn2, eqn3, eqn4, eqn5)
    
    
def solve(engine: EngineModel, ox_tank: PropTank, fuel_tank: PropTank):
    runtime = 60  # [s] Overall runtime of 15 seconds
    dt = 0.1     # 10 ms timestep length
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
    # Ox tank properties
    ox_P_graph = [0 for _ in range(t_range.size)]
    ox_T_graph = [0 for _ in range(t_range.size)]
    ox_mdot_graph = [0 for _ in range(t_range.size)]
    # Fuel tank properties
    fuel_P_graph = [0 for _ in range(t_range.size)]
    fuel_T_graph = [0 for _ in range(t_range.size)]
    fuel_mdot_graph = [0 for _ in range(t_range.size)]
    impulse = 0
    
    last_index = t_range.size-1
    for i in range(t_range.size):
        init_guess = tuple((8, 4, 1500, 12500, 2.1e6))
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
        ox_P_graph[i], ox_T_graph[i] = ox_tank.gas_state.P, ox_tank.gas_state.T
        ox_mdot_graph[i] = mdot_o
        fuel_P_graph[i], fuel_T_graph[i] = fuel_tank.gas_state.P, fuel_tank.gas_state.T
        fuel_mdot_graph[i] = mdot_f
        impulse += F_t*dt
        # If critical choked flow pressure ratio is breached, we've reached the end of the burn
        if (choked_flow_violated(P_c, (mdot_o/mdot_f), engine.P_a) or tanks_empty(ox_tank, fuel_tank)):
            if (tanks_empty(ox_tank, fuel_tank)): info = "tanks empty"
            else: info = "critical pressure ratio breached"
            print("**End of burn detected ({0}) at P_c = {1:.2f} psia, t = {2} s".format(info, P_c/PSI_TO_PA, i*dt))
            # Since we ended the data collection early, should shorten the data arrays
            t_range = t_range[:i+1]
            F_graph, Pc_graph, Cstar_graph = F_graph[:i+1], Pc_graph[:i+1], Cstar_graph[:i+1]
            ox_P_graph, ox_T_graph, ox_mdot_graph = ox_P_graph[:i+1], ox_T_graph[:i+1], ox_mdot_graph[:i+1]
            fuel_P_graph, fuel_T_graph, fuel_mdot_graph = fuel_P_graph[:i+1], fuel_T_graph[:i+1], fuel_mdot_graph[:i+1]
            last_index = i
            break
    
    # Print initial/final state of the system
    print("Thrust: {0:.2f} kN | Chamber pressure: {1:.2f} psia | Total mdot: {2:.2f} kg/s | O/F: {3:.2f}".format(
        F_graph[0]/1000, Pc_graph[0]/PSI_TO_PA, ox_mdot_graph[0]+fuel_mdot_graph[0], ox_mdot_graph[0]/fuel_mdot_graph[0]))
    ox_str = ox_tank.get_state_string()
    fuel_str = fuel_tank.get_state_string()
    print("----- Final system state: -----")
    print("Oxdizer [LOX]:" + "\n\t" + ox_str)
    print("Fuel [RP-1]:" + "\n\t" + fuel_str)
    print("Thrust: {0:.2f} kN | Chamber pressure: {1:.2f} psia | Total mdot: {2:.2f} kg/s | O/F: {3:.2f}".format(
        F_graph[last_index]/1000, Pc_graph[last_index]/PSI_TO_PA, ox_mdot_graph[last_index]+fuel_mdot_graph[last_index],
        ox_mdot_graph[last_index]/fuel_mdot_graph[last_index]))
    print("Total impulse through burn: {0:.3f} kN s".format(impulse))
    print("Residual oxidizer: {0:.3f} kg".format(ox_tank.V_prop*ox_tank.rho_prop))
    print("Residual fuel: {0:.3f} kg".format(fuel_tank.V_prop*fuel_tank.rho_prop))
    
    # Graph values
    # plt.rc("font", size=14)
    fig1, axs1 = plt.subplots(4,1)
    fig1.set_size_inches((8, 6))
    fig1.suptitle("ME-5 Transient Blowdown Engine Performance")
    axs1[0].plot(t_range, np.array(F_graph)/1000)
    axs1[1].plot(t_range, np.array(Pc_graph)/PSI_TO_PA)
    axs1[2].plot(t_range, np.array(Cstar_graph))
    axs1[3].plot(t_range, np.divide(np.array(ox_mdot_graph), np.array(fuel_mdot_graph)))
    plt.xlabel("Time [s]")
    axs1.flat[0].set(ylabel = "Thrust [kN]")
    axs1.flat[1].set(ylabel = "P (chamber) [psia]")
    axs1.flat[2].set(ylabel = "C* (eff) [m/s]")
    axs1.flat[3].set(ylabel = "O/F Ratio")
    axs1[0].grid()
    axs1[1].grid()
    axs1[2].grid()
    axs1[3].grid()
    
    fig2, axs2 = plt.subplots(3,1)
    fig2.set_size_inches((8, 6))
    fig2.suptitle("Propellant Tank Characteristics")
    axs2[0].plot(t_range, np.array(ox_P_graph)/PSI_TO_PA, label="Ox")
    axs2[0].plot(t_range, np.array(fuel_P_graph)/PSI_TO_PA, label="Fuel")
    axs2[1].plot(t_range, np.array(ox_T_graph), label="Ox")
    axs2[1].plot(t_range, np.array(fuel_T_graph), label="Fuel")
    axs2[2].plot(t_range, np.array(ox_mdot_graph), label="Ox")
    axs2[2].plot(t_range, np.array(fuel_mdot_graph), label="Fuel")
    plt.xlabel("Time [s]")
    axs2.flat[0].set(ylabel = "P (Ullage) [psia]")
    axs2.flat[1].set(ylabel = "T (Ullage) [K]")
    axs2.flat[2].set(ylabel = "Mass flow rate [kg/s]")
    axs2[0].legend(loc="upper right")
    axs2[1].legend(loc="upper right")
    axs2[2].legend(loc="upper right")
    axs2[0].grid()
    axs2[1].grid()
    axs2[2].grid()
    
    # Write data to output file
    with open("thrust_curve.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(["Thrust (N)", "Time (s)"])
        data = [t_range, F_graph]
        data = np.asarray(data).transpose()
        for row in range(len(t_range)):
            writer.writerow(data[row,:])
    plt.show()


if __name__ == "__main__":
    warnings.filterwarnings("ignore")  # Suppress scipy.optimize warnings
    rp1_rho = 790   # Typically 810 to 1020 [kg/m^3]
    lox_rho = 1140  # At boiling point [kg/m^3]
    # Initial COPV: ~1000 psia, room temperature, 50 L
    # copv = COPV(7e6, 298, 0.05, dt)
    me_5 = EngineModel()
    # Ox tank is 97.15 L with 28.537 L of ullage at 1200 psi and 71.4K ullage
    # ox_tank = PropTank(97.15, (97.15-28.537), lox_rho, 1200, 185.1, 0.000075160) 
    # Fuel tank is 66.26 L with 19.784 L of ullage at 1200 psi and 185K ullage
    # fuel_tank = PropTank(66.26, (66.26-19.784), rp1_rho, 1200, 185.1, 0.000044416)
    
    # Ox tank is 97.15 L with 28.537 L of ullage at 1200 psi and 71.4K ullage
    ox_tank = PropTank(97.15, (97.15-28.537), lox_rho, 500, 185.1, 0.000075160) 
    # Fuel tank is 66.26 L with 19.784 L of ullage at 1200 psi and 185K ullage
    fuel_tank = PropTank(66.26, (66.26-19.784), rp1_rho, 500, 185.1, 0.000044416)
    # Print initial state of the system
    ox_str = ox_tank.get_state_string()
    fuel_str = fuel_tank.get_state_string()
    print("----- Initial system state: -----")
    print("Oxdizer [LOX]:" + "\n\t" + ox_str)
    print("Fuel [RP-1]:" + "\n\t" + fuel_str)
    solve(me_5, ox_tank, fuel_tank)
