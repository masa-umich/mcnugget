# Full burn duration engine simulator
# Generates a thrust curve as a function of time
# For a techincal walkthrough, see ./engine_sim_explained.md
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
LBM_TO_KG = 1/2.205
GN2_RHO_STP = 1.2506
def f_to_kelvin(temp): return (temp-32)*(5/9)+273.15
def scfm_to_mdot(scfm): return (scfm/GN2_RHO_STP)*LBM_TO_KG
def mdot_to_scfm(mdot): return (mdot/LBM_TO_KG)*GN2_RHO_STP
os.environ['RPPREFIX'] = r'/home/jasonyc/masa/REFPROP-cmake/build'
cea = CEA_Obj(oxName="LOX", fuelName="RP1")
def get_reg_curve(inlet_p: float, mdot: float) -> float:
    """
    Return the outlet pressure of the dome regulator given a mass flow and inlet pressure.
    These explicit functions are data interpolations from our regulator manufacturer, Premier,
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
    """
    coeff_a = 0
    raise NotImplementedError
