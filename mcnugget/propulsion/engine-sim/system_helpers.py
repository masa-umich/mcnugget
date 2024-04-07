# Includes helpers to solve the system of equations for both engine and feed 

import numpy as np
from scipy.optimize import fsolve
from rocketcea.cea_obj import CEA_Obj
import constants as consts

cea = CEA_Obj(oxName="LOX", fuelName="RP1")
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15
def scfm_to_mdot(scfm): return ((scfm/60)*consts.GN2_RHO_IMP)*consts.LBM_TO_KG
def mdot_to_scfm(mdot): return ((mdot/consts.LBM_TO_KG)/consts.GN2_RHO_IMP)*60


def tca_system_eqns(params: tuple, *const_params: tuple):
    # System of equations that represent the engine
    mdot_o, mdot_f, c_star, F_t, P_c = params
    cda_o, rho_o, P_o, cda_f, rho_f, P_f, pc_ideal, A_t, C_F, C_star_eff = const_params
    # Squaring the CdA equation to avoid sqrt()
    eqn1 = cda_o**2 * (2*rho_o*(P_o - P_c)) - mdot_o**2
    eqn2 = cda_f**2 * (2*rho_f*(P_f - P_c)) - mdot_f**2
    eqn3 = (get_cea_c_star(mdot_o/mdot_f, pc_ideal) * C_star_eff) - c_star
    eqn4 = F_t/(A_t*C_F) - P_c
    eqn5 = (mdot_o+mdot_f) * c_star * C_F - F_t
    return (eqn1, eqn2, eqn3, eqn4, eqn5)


def feed_system_eqns(params: tuple, *const_params: tuple):
    E, T, p, m, mdot = params
    e_prev, p_prev, m_prev, cv, T_prev, Z_prev, V_prev = const_params[0:7]
    p_copv, h_copv, vdot_liq, dt, reg_cda = const_params[7:]
    new_V = V_prev + vdot_liq*dt
    cp = cv + consts.GN2_R
    gamma = cp/cv
    # Energy conservation equation: note that E is extensive internal energy
    eqn1 = e_prev*m_prev + (mdot)*dt*h_copv - p_prev*vdot_liq*dt - E
    eqn2 = ((E + p*new_V)/cv) - T
    eqn3 = get_reg_outlet(p_copv, mdot, reg_cda, gamma, T_prev) - p
    eqn4 = (p*new_V)/(Z_prev*consts.GN2_R*T) - m
    eqn5 = m_prev + (mdot)*dt - m
    # eqn6 = (E - e_prev*m_prev) + p_prev*vdot_liq*dt - T_prev*(cp*np.log(T/T_prev) - 
        # consts.GN2_R*np.log(p/p_prev))
    return (eqn1, eqn2, eqn3, eqn4, eqn5)


def get_cea_c_star(of_ratio: float, pc_ideal: float):
    # Return c_star according to CEA [m/s]
    return consts.FT_TO_M*cea.get_Cstar(Pc=(pc_ideal/consts.PSI_TO_PA), MR=of_ratio)


def get_reg_outlet(inlet_p: float, mdot: float, reg_cda, gamma, T_prev) -> float:
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
    To model the seat-load drop, use (200/(x+6))+470 for SCFM < 50
    Note: Given 4.5 ksi and room temp, max choked mdot of a 1" ID pipe is ~36 kg/s, and 
    500 psi + 1" ID is ~4 kg/s (7200 SCFM). Thus, we will lose control of the dome regulator
    far before pipe choking becomes an issue, i.e. 850 SCFM (0.467 kg/s) is the upper limit.
    """
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
    
    scfm_val = mdot_to_scfm(mdot)
    inlet_ksi = (inlet_p/consts.PSI_TO_PA)/1000
    
    if (scfm_val < 50):
        return ((200/(scfm_val+6))+470)*consts.PSI_TO_PA
    
    """
    if (scfm_val > 850):
        scfm_val = mdot_to_scfm(inlet_p*reg_cda*np.sqrt(gamma/(consts.GN2_R*T_prev)) * (
            2/(gamma+1)) ** ((gamma+1)/(2*gamma-2)))
        print(scfm_val)
    """
    
    # We want a linear mapping from input range [1,4.5] to output range [35,5]
    # \frac{\left(o_{max}-o_{min}\right)}{i_{max}-i_{min}}\cdot\left(x-i_{min}\right)+o_{min}
    # https://stackoverflow.com/questions/5731863/mapping-a-numeric-range-onto-another
    coeff_a = ((5-35)/(4.5-1))*(inlet_ksi-1) + 35
    
    # We want a parabolic mapping from input range [1,4.5] to output range [750,1310]
    # \frac{\left(o_{max}-o_{min}\right)\left(x-i_{min}\right)^{2}}
    #     {\left(i_{max}-i_{min}\right)^{2}}+o_{min}
    # https://www.desmos.com/calculator/ewnq4hyrbz
    coeff_b = ((1310-750)*(inlet_ksi-1)**2)/(4.5-1)**2 + 750
    return (coeff_a*np.tan(-1*scfm_val/coeff_b) + 475) * consts.PSI_TO_PA
