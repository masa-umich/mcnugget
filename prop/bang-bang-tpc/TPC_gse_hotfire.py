import os, numpy as np
import matplotlib.pyplot as plt
from matplotlib import interactive
from scipy.optimize import fsolve
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
from numpy import genfromtxt

# interactive(True)

# TPC Orifice Area Calculator
# Calculates the area needed for both fuel and LOx side TPC for varying COPV Pressure
# using real-gas properties

# CHANGABLE VARIABLES AT THE BOTTOM. YOU SHOULD TAKE YOURSELF THERE, NOW!

# Unit conversion values
IN_TO_M = 1 / 39.37
PSI_TO_PA = 6894.757
L_TO_M3 = 0.001
FT_TO_M = 1 / 3.281

class Orifice:
    # This class keeps track of orifice values (all estimated)
    def __init__(self, Cd: float, Cf: float, CdA_valve: float):
        self.Cd = Cd # Orifice Cd
        self.Cf = Cf # Orifice collapse factor
        self.CdA_valve = CdA_valve # Orifice Area


class Liquid:
    # This class is purely to reference fuel and LOx mass and volumteric flow rates (constant)
    def __init__(self, mdot_F0: float, mdot_L0: float, rho_F: float, rho_L: float):
        self.mdot_F = mdot_F0
        self.mdot_L = mdot_L0
        self.Vdot_F = mdot_F0/rho_F
        self.Vdot_L = mdot_L0/rho_L


class Gas:
    # Static class variables for running REFPROP across all instances
    _RP = REFPROPFunctionLibrary(os.environ["RPPREFIX"])
    _RP.SETPATHdll(os.environ["RPPREFIX"])
    _MASS_BASE_SI = _RP.GETENUMdll(0, "MASS BASE SI").iEnum

    @property
    def RP(self):
        return type(self)._RP

    @property
    def MASS_BASE_SI(self):
        return type(self)._MASS_BASE_SI

    def __init__(self, P_0: float, T_0: float, V_0: float, gas: str = "Nitrogen"):
        self.gas = gas
        self.P = P_0  # [Pa]
        self.T = T_0  # [K]
        self.V = V_0  # [m^3]
        self.internal_energy = self.RP.REFPROPdll(
            gas, "PT", "E", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]
        self.density = self.RP.REFPROPdll(
            gas, "PT", "D", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]
        self.gamma = self.RP.REFPROPdll(
            gas, "PT", "CP/CV", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]
        self.enthalpy = self.RP.REFPROPdll(
            gas, "PT", "H", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]
        # Entropy is assumed to stay constant
        self.entropy = self.RP.REFPROPdll(
            gas, "PT", "S", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]
        self.compressibility = self.RP.REFPROPdll(
            gas, "PT", "Z", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]
        self.specific_heat = self.RP.REFPROPdll(
            gas, "PT", "Cp", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]
        self.m = self.density * V_0  # Mass of gas [kg]
        self.R = self.RP.REFPROPdll(
            gas, "PT", "R", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]  # Gas constant [J/kg-K]

    # Given a new pressure, updates the state of the COPV assuming constant entropy 
    # USE FOR COPV
    def update_state_COPV(self, P: float, V_0: float):
        self.P = P
        self.V = V_0  # [m^3]
        self.internal_energy = self.RP.REFPROPdll(
            self.gas, "PS", "E", self.MASS_BASE_SI, 0, 0, self.P, self.entropy, [1.0]
        ).Output[0]
        self.density = self.RP.REFPROPdll(
            self.gas, "PS", "D", self.MASS_BASE_SI, 0, 0, self.P, self.entropy, [1.0]
        ).Output[0]
        self.T = self.RP.REFPROPdll(
            self.gas, "PS", "T", self.MASS_BASE_SI, 0, 0, self.P, self.entropy, [1.0]
        ).Output[0]
        self.gamma = self.RP.REFPROPdll(
            self.gas, "PS", "CP/CV", self.MASS_BASE_SI, 0, 0, self.P, self.entropy, [1.0]
        ).Output[0]
        self.enthalpy = self.RP.REFPROPdll(
            self.gas, "PS", "H", self.MASS_BASE_SI, 0, 0, self.P, self.entropy, [1.0]
        ).Output[0]
        self.compressibility = self.RP.REFPROPdll(
            self.gas, "PS", "Z", self.MASS_BASE_SI, 0, 0, self.P, self.entropy, [1.0]
        ).Output[0]
        self.specific_heat = self.RP.REFPROPdll(
            self.gas, "PS", "Cp", self.MASS_BASE_SI, 0, 0, self.P, self.entropy, [1.0]
        ).Output[0]
        self.R = self.RP.REFPROPdll(
            self.gas, "PS", "R", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]  # Gas constant [J/kg-K]
        self.m = self.density * V_0  # Mass of gas [kg

    # Given a new internal energy, updates ullage state assuming constant pressure
    # USE FOR ULLAGE
    def update_state_ullage(self, U: float):
        self.internal_energy = U
        self.entropy = self.RP.REFPROPdll(
            self.gas, "PE", "S", self.MASS_BASE_SI, 0, 0, self.P, self.internal_energy, [1.0]
        ).Output[0]
        self.density = self.RP.REFPROPdll(
            self.gas, "PE", "D", self.MASS_BASE_SI, 0, 0, self.P, self.internal_energy, [1.0]
        ).Output[0]
        self.T = self.RP.REFPROPdll(
            self.gas, "PE", "T", self.MASS_BASE_SI, 0, 0, self.P, self.internal_energy, [1.0]
        ).Output[0]
        self.gamma = self.RP.REFPROPdll(
            self.gas, "PE", "G", self.MASS_BASE_SI, 0, 0, self.P, self.internal_energy, [1.0]
        ).Output[0]
        self.enthalpy = self.RP.REFPROPdll(
            self.gas, "PE", "H", self.MASS_BASE_SI, 0, 0, self.P, self.internal_energy, [1.0]
        ).Output[0]
        self.compressibility = self.RP.REFPROPdll(
            self.gas, "PE", "Z", self.MASS_BASE_SI, 0, 0, self.P, self.internal_energy, [1.0]
        ).Output[0]
        self.specific_heat = self.RP.REFPROPdll(
            self.gas, "PE", "Cp", self.MASS_BASE_SI, 0, 0, self.P, self.internal_energy, [1.0]
        ).Output[0]
        self.R = self.RP.REFPROPdll(
            self.gas, "PE", "R", self.MASS_BASE_SI, 0, 0, self.P, self.T, [1.0]
        ).Output[0]  # Gas constant [J/kg-K]

    def update_mass_volume(self, m: float, V: float):
        self.m = m
        self.V = V


def system_equations(params: tuple, *constants: tuple):
    # System of equations that represent the ullage states. The asterisk in `constants` packs the tuple
    V_ull_F,m_ull_F,mdot_ull_F,T_ull_F,E_ull_F,V_ull_L,m_ull_L,mdot_ull_LOx,T_ull_L,E_ull_L = params
    V_ull_F_prev,Vdot_F,dt,Z_F,R_F,P_F,m_ull_F_prev,N2_F_specific_heat,E_ull_F_prev,\
    N2_C_enthalpy,V_ull_L_prev,Vdot_L,Z_L,R_L,P_L,m_ull_L_prev,N2_L_specific_heat,\
    E_ull_L_prev = constants
    eqn1 = V_ull_F - V_ull_F_prev - Vdot_F*dt,
    eqn2 = m_ull_F*Z_F*R_F*mdot_ull_F - P_F*V_ull_F
    eqn3 = m_ull_F - m_ull_F_prev - mdot_ull_F*dt,
    eqn4 = T_ull_F*N2_F_specific_heat*m_ull_F - E_ull_F - P_F*V_ull_F,
    eqn5 = E_ull_F - E_ull_F_prev - mdot_ull_F*N2_C_enthalpy*dt + P_F*Vdot_F*dt,
    eqn6 = V_ull_L - V_ull_L_prev - Vdot_L*dt,
    eqn7 = m_ull_L*Z_L*R_L*mdot_ull_LOx - P_L*V_ull_L,
    eqn8 = m_ull_L - m_ull_L_prev - mdot_ull_LOx*dt,
    eqn9 = T_ull_L*N2_L_specific_heat*m_ull_L - E_ull_L - P_L*V_ull_L,
    eqn10 = E_ull_L - E_ull_L_prev - mdot_ull_LOx*N2_C_enthalpy*dt + P_L*Vdot_L*dt,
    return (eqn1, eqn2, eqn3, eqn4, eqn5, eqn6, eqn7, eqn8, eqn9, eqn10)

def get_constants(Fuel_ullage: Gas, LOx_ullage: Gas, COPV: Gas, Liquids: Liquid, dt: float):
    # Returns a tuple of the constants necessary for the system of equations
    c1 = Fuel_ullage.V
    c2 = Liquids.Vdot_F
    c3 = dt
    c4 = Fuel_ullage.compressibility
    c5 = Fuel_ullage.R
    c6 = Fuel_ullage.P
    c7 = Fuel_ullage.m
    c8 = Fuel_ullage.specific_heat
    c9 = Fuel_ullage.internal_energy*Fuel_ullage.m
    c10 = COPV.enthalpy
    c11 = LOx_ullage.V
    c12 = Liquids.Vdot_L
    c13 = LOx_ullage.compressibility
    c14 = LOx_ullage.R
    c15 = LOx_ullage.P
    c16 = LOx_ullage.m
    c17 = LOx_ullage.specific_heat
    c18 = LOx_ullage.internal_energy*LOx_ullage.m
    return tuple((c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14,c15,c16,c17,c18))

def solve(Fuel_ullage: Gas, LOx_ullage: Gas, COPV: Gas, Liquids: Liquid, orifice: Orifice):
    time_elapsed = 0 # Keeps track of time since start [s]
    dt = 0.006 # Time per timestep [s]
    N = 1000 # Outer loop number of iterations
    n = 100 # Inner loop iterations
    P_C = np.zeros(N) # COPV pressure to graph

    # Area arrays for constant pressure and area needed to stay below 10 psi/valve actuation time rate of change, in in^2
    Isentrope_F = np.zeros(N)
    Isentrope_L = np.zeros(N)
    Isoe_plus10_F = np.zeros(N)
    Isoe_plus10_L = np.zeros(N)
    t_close = np.zeros(N)
    t_open = np.zeros(N)

    # Ullage mdots used later
    mdot_ull_F_array = np.zeros(N)
    mdot_ull_LOx_array = np.zeros(N)

    COPV_pressures = np.linspace(P_F/((2/2.4)**(1.4/0.4)), P_COPV, N)

    #IDEAL GAS CALCS
    C_sqrt = (
        COPV.P * COPV.density * COPV.gamma
        * (2/(COPV.gamma+1))**((COPV.gamma+1)/(COPV.gamma-1))
    )**0.5

    A_fuel_init = (dpdt*V0_F+Fuel_ullage.P*(mdot_Fuel/rp1_rho))/(orifice.Cd*Fuel_ullage.compressibility*Fuel_ullage.R*Fuel_ullage.T*C_sqrt)*1550
    A_lox_init = Cf*(dpdt*V0_L+LOx_ullage.P*(mdot_LOx/LOx_rho))/(orifice.Cd*LOx_ullage.compressibility*LOx_ullage.R*LOx_ullage.T*C_sqrt)*1550

    print("IDEAL GAS CALCS")
    print("Initial Max Fuel Area: ", A_fuel_init)
    print("Initial Max LOx Area: ", A_lox_init)
    #END IDEAL CALCS

    for y in range(N):
        # Previous COPV state values
        E_C_prev = COPV.internal_energy*COPV.m
        m_C_prev = COPV.m
        
        # Update COPV state
        COPV.update_state_COPV(COPV_pressures[(N - 1) - y], V_COPV)

        # Keep track of COPV pressure to plot [psi]
        P_C[(N - 1) - y] = COPV.P / PSI_TO_PA
        # Change in COPV mass and energy
        delta_m_C = m_C_prev - COPV.m
        delta_E_C = E_C_prev - (COPV.internal_energy*COPV.m)

        # Energy in each ullage
        E_ullage_Fuel = Fuel_ullage.internal_energy * Fuel_ullage.m
        E_ullage_LOx = LOx_ullage.internal_energy * LOx_ullage.m

        # Previous tank state values
        V_Ull_F_prev = Fuel_ullage.V
        V_Ull_L_prev = LOx_ullage.V
        E_Ull_F_prev = Fuel_ullage.internal_energy * Fuel_ullage.m
        E_Ull_L_prev = LOx_ullage.internal_energy * LOx_ullage.m
        m_Ull_F_prev = Fuel_ullage.m
        m_Ull_L_prev = LOx_ullage.m

        # set up needed values for inner loop, previous ullage volume gets used later
        # so I added a new variable so the previous value remains untouched
        Z_Fuel = Fuel_ullage.compressibility
        Z_LOx = LOx_ullage.compressibility
        R_Fuel = Fuel_ullage.R
        R_LOx = LOx_ullage.R
        V_Ull_F_Loop = V_Ull_F_prev
        V_Ull_L_Loop = V_Ull_L_prev

        # Set up and solve system of equations
        init_guess = tuple((10,10,10,20000,1200000,190,100,20,1000,10000000)) # Guesses for fsolve

        for z in range(n):
            
            # Solve the system for the fuel tank state, x[0] is volume, x[1] is mass, x[2] is mdot,
            # x[3] is temperature, x[4] is total energy, add 5 to each to get the LOx variables
            def state_func(x):
                return [
                    x[0] - V_Ull_F_Loop - Liquids.Vdot_F * dt,
                    x[1] * Z_Fuel * R_Fuel * x[3] - Fuel_ullage.P * x[0],
                    x[1] - m_Ull_F_prev - x[2] * dt,
                    x[3] * Fuel_ullage.specific_heat * x[1] - x[4] - Fuel_ullage.P * x[0],
                    x[4] - E_Ull_F_prev - x[2] * COPV.enthalpy * dt + Fuel_ullage.P * Liquids.Vdot_F * dt,
                    x[5] - V_Ull_L_Loop - Liquids.Vdot_L * dt,
                    x[6] * Z_LOx * R_LOx * x[8] - LOx_ullage.P * x[5],
                    x[6] - m_Ull_L_prev - x[7] * dt,
                    x[8] * LOx_ullage.specific_heat * x[6] - x[9] - LOx_ullage.P * x[5],
                    x[9] - E_Ull_L_prev - x[7] * COPV.enthalpy * dt + LOx_ullage.P * Liquids.Vdot_L * dt,
                ]

            state = fsolve(state_func, init_guess, xtol=1e-9)

            V_Ull_F_Loop = state[0]
            m_Ull_F_prev = state[1]
            mdot_ull_F_array[(N - 1) - y] = state[2]
            T_Ull_F_prev = state[3]
            E_Ull_F_prev = state[4]
            V_Ull_L_Loop = state[5]
            m_Ull_L_prev = state[6]
            mdot_ull_LOx_array[(N - 1) - y] = orifice.Cf * state[7]
            T_Ull_L_prev = state[8]
            E_Ull_L_prev = state[9]

        # Amounts of mass and energy flowing into each ullage
        delta_m_fuelullage = delta_m_C * (
            mdot_ull_F_array[(N - 1) - y] 
            / (mdot_ull_F_array[(N - 1) - y] + mdot_ull_LOx_array[(N - 1) - y])
        )

        delta_m_LOxullage = delta_m_C * (
            mdot_ull_LOx_array[(N - 1) - y] 
            / (mdot_ull_F_array[(N - 1) - y] + mdot_ull_LOx_array[(N - 1) - y])
        )

        delta_E_fuelullage = delta_E_C * (
            mdot_ull_F_array[(N - 1) - y] 
            / (mdot_ull_F_array[(N - 1) - y] + mdot_ull_LOx_array[(N - 1) - y])
        )

        delta_E_LOxullage = delta_E_C * (
            mdot_ull_LOx_array[(N - 1) - y] 
            / (mdot_ull_F_array[(N - 1) - y] + mdot_ull_LOx_array[(N - 1) - y])
        )

        delta_t = delta_m_fuelullage / mdot_ull_F_array[(N - 1) - y]

        # Update mass, volume, and energy of each ullage
        Fuel_ullage.m += delta_m_fuelullage
        LOx_ullage.m += delta_m_LOxullage
        Fuel_ullage.V += delta_m_fuelullage/Fuel_ullage.density
        LOx_ullage.V += delta_m_LOxullage/LOx_ullage.density
        E_ullage_Fuel = (
            E_ullage_Fuel + delta_E_fuelullage - Fuel_ullage.P * (Fuel_ullage.V - V_Ull_F_prev)
        )
        E_ullage_LOx = (
            E_ullage_LOx + delta_E_LOxullage - LOx_ullage.P * (LOx_ullage.V - V_Ull_L_prev)
        )

        # Specific Internal Energy updates
        Fuel_ullage_e = E_ullage_Fuel / Fuel_ullage.m
        LOx_ullage_e = E_ullage_LOx / LOx_ullage.m

        # Update Tank States
        Fuel_ullage.update_state_ullage(Fuel_ullage_e)
        LOx_ullage.update_state_ullage(LOx_ullage_e)
        
        #print(V_Ull_F_Loop, m_Ull_F_prev, mdot_ull_F_array[(N - 1) - y], T_Ull_F_prev, E_Ull_F_prev, V_Ull_L_Loop, m_Ull_L_prev, mdot_ull_LOx_array[(N - 1) - y], T_Ull_L_prev, E_Ull_L_prev)

        # Area Calcs
        C_mdot = (
        orifice.Cd
        * (
            COPV.gamma
            * COPV.density
            * COPV.P
            * (2 / (COPV.gamma + 1)) ** ((COPV.gamma + 1) / (COPV.gamma - 1))
        )
        ** 0.5
        )
        Isentrope_F[(N - 1) - y] = (mdot_ull_F_array[(N - 1) - y] / C_mdot) * 1550
        Isentrope_L[(N - 1) - y] = (mdot_ull_LOx_array[(N - 1) - y] / C_mdot) * 1550
        Isoe_plus10_F[(N - 1) - y] = (dpdt * (Fuel_ullage.V) + (delta_m_fuelullage / Fuel_ullage.density / delta_t) * Fuel_ullage.P)/(C_mdot * R_Fuel * Fuel_ullage.T * Z_Fuel) * 1550
        Isoe_plus10_L[(N - 1) - y] = (dpdt * (LOx_ullage.V) + (delta_m_LOxullage / LOx_ullage.density / delta_t) * LOx_ullage.P)/(C_mdot * R_LOx * LOx_ullage.T * Z_LOx) * 1550
        #t_close[(N - 1) - y] = response_time - P_bound*Fuel_ullage.V/(Fuel_ullage.P*(delta_m_fuelullage / Fuel_ullage.density / delta_t))
        #t_open[(N - 1) - y] = response_time - P_bound/(mdot_ull_F_array[(N - 1) - y]*Fuel_ullage.compressibility*Fuel_ullage.T*R_Fuel/Fuel_ullage.V - Fuel_ullage.P*(delta_m_fuelullage / Fuel_ullage.density / delta_t)/Fuel_ullage.V)
        #print((Fuel_ullage.V - V0_F) / (mdot_Fuel / rp1_rho), COPV.P / PSI_TO_PA, Fuel_ullage.T,Fuel_ullage.V)
    # Graph fuel orifice area
    CdA_Valve = orifice.CdA_valve

    plt.figure(1)
    ideal_fuel = plt.plot(P_C, Isentrope_F, "-r", label="MINIMUM AREA")
    plus_10_F = plt.plot(P_C, Isoe_plus10_F, "--r", label="MAXIMUM AREA")

    one_valve = plt.plot(
        [P_C[0], P_C[N - 1]], [CdA_Valve*0.35, CdA_Valve*0.35], "-g", label="Cv = 0.2625"
    )

    two_valve = plt.plot(
        [P_C[0], P_C[N - 1]], [CdA_Valve*0.7, CdA_Valve*0.7], "-g", label="Cv = 0.5250"
    )

    #three_valve = plt.plot(
       # [P_C[0],P_C[N-1]], [CdA_Valve, CdA_Valve], "-g", label="Cv = 0.75"
    #)
    plt.xlabel("COPV Pressure (psi)")
    plt.ylabel("Orifice Area (in^2)")
    plt.title("Fuel TPC Area")
    plt.legend()

    plt.figure(2)
    ideal_LOx = plt.plot(P_C, Isentrope_L, "-b", label="MINIMUM AREA")
    plus_10_F = plt.plot(P_C, Isoe_plus10_L, "--b", label="MAXIMUM AREA")

    one_valve = plt.plot(
        [P_C[0], P_C[N - 1]], [CdA_Valve, CdA_Valve], "-g", label="Cv = 0.75"
    )

    two_valve = plt.plot(
        [P_C[0], P_C[N - 1]], [CdA_Valve*2, CdA_Valve*2], "-g", label="Cv = 1.5"
    )

    #three_valve = plt.plot(
       # [P_C[0],P_C[N-1]], [CdA_Valve, CdA_Valve], "-g", label="Cv = 2.25"
    #)

    #four_valve = plt.plot(
       # [P_C[0],P_C[N-1]], [CdA_Valve*3, CdA_Valve*3], "-g", label="Cv = 3"
    #)
    plt.xlabel("COPV Pressure (psi)")
    plt.ylabel("Orifice Area")
    plt.title("LOx TPC Area")
    plt.legend()

    plt.show()

if __name__ == "__main__":
    rp1_rho = 1000  # Typically 810 to 1020 [kg/m^3]
    LOx_rho = 1140  # At boiling point [kg/m^3]
    # Estimated Orifice Cd, collapse factor, and orifice area
    Cd = 0.81
    Cf = 1.5
    CdA_Valve = (0.75 / (27.66))

    # mdots out at T0, in kg/s
    mdot_Fuel = 1.96 # <-- Fuel flowrate into engine
    mdot_LOx = 4.17 # <-- Oxidizer flowrate into engine

    # Flow rates
    liquid = Liquid(mdot_Fuel,mdot_LOx,rp1_rho,LOx_rho)

    # Orifice values
    orifice = Orifice(Cd,Cf,CdA_Valve)

    # Starting COPV, Fuel ullage, and LOx Ullage states
    T0_F = 290 # [K] 
    T0_L = 160 # [K]
    P_F = 500 * 6894.76 # [Pa] 
    P_L = 500 * 6894.76 # [Pa]
    P_COPV = 4000 * 6894.76 # [Pa]

    # Pressure bound below nominal 
    P_bound = 10 * PSI_TO_PA # [Pa]

    # Response time of the system
    response_time = 0.162 # [sec]

    # Maximum allowable pressure rate of change
    dpdt = P_bound/response_time

    # Initial volume of gas, in [m^3]
    V0_F = (18 / 1000)
    V0_L = (32 / 1000) 
    V_COPV = 36.0 / 1000

    COPV = Gas(P_COPV,T0_F,V_COPV)
    Fuel_ullage = Gas(P_F,T0_F,V0_F)
    LOx_ullage = Gas(P_L,T0_L,V0_L)

    solve(Fuel_ullage,LOx_ullage,COPV,liquid,orifice)