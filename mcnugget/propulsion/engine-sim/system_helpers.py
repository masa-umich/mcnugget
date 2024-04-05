# Includes helpers to solve the system of equations for both engine and feed 

from scipy.optimize import fsolve
from rocketcea.cea_obj import CEA_Obj
import constants as consts

cea = CEA_Obj(oxName="LOX", fuelName="RP1")


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
    pass



def get_cea_c_star(of_ratio: float, pc_ideal: float):
    # Return c_star according to CEA [m/s]
    return consts.FT_TO_M*cea.get_Cstar(Pc=(pc_ideal/consts.PSI_TO_PA), MR=of_ratio)
