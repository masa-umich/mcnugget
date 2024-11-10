import matplotlib.pyplot as plt
import numpy as np
import scipy
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import os

# https://refprop-docs.readthedocs.io/en/latest/DLL/high_level.html#f/_/REFPROPdll


# created by Ichiro Ausin
# Place to store functions for refprop

# If the RPPREFIX environment variable is not already set by your installer (e.g., on windows), 
# then uncomment this line and set the absolute path to the location of your install of 
# REFPROP
# Need to set the following line in each of your code programs
os.environ['RPPREFIX'] = r'C:\Program Files (x86)\REFPROP'

def fluid_temp_from_P_D(fluid, p_pa, density):
    """
    Inputs:
        fluid: string of fluid to analyze 
        p_pa: pressure of the fluid, in Pascals
        density: density of the fluid, in kg/m^3
    
    Output: temperature of the gas
    """
    RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    RP.SETPATHdll(os.environ['RPPREFIX'])
    MASS_BASE_SI = RP.GETENUMdll(0,"MASS BASE SI").iEnum
    r = RP.REFPROPdll(fluid,"PD","T",MASS_BASE_SI, 0,0,p_pa , density, [1.0])
    return r.Output[0]

def fluid_density_from_P_T(fluid, p_pa, temperature):
    """
    Inputs:
        fluid: string of fluid to analyze
        p_pa: pressure of the fluid, in Pascals
        temperature: temperature of the fluid, in Kelvin
    
    Output: density of the gas
    """
    RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    RP.SETPATHdll(os.environ['RPPREFIX'])
    MASS_BASE_SI = RP.GETENUMdll(0,"MASS BASE SI").iEnum
    r = RP.REFPROPdll(fluid,"TP","D",MASS_BASE_SI, 0,0,temperature, p_pa , [1.0])
    return r.Output[0]

def fluid_pressure_from_T_D(fluid, temperature, density):
    """
    Inputs:
        fluid: string of fluid to analyze
        temperature: temperature of the fluid, in Kelvin
        density: density of the fluid kg/m^3
    
    Output: pressure of the gas
    """
    RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    RP.SETPATHdll(os.environ['RPPREFIX'])
    MASS_BASE_SI = RP.GETENUMdll(0,"MASS BASE SI").iEnum
    r = RP.REFPROPdll(fluid,"TD","P",MASS_BASE_SI, 0,0,temperature, density, [1.0])
    return r.Output[0]

def fluid_gamma_from_P_T(fluid, p_pa, temperature):
    """
    Inputs:
        fluid: string of fluid to analyze
        p_pa: pressure of the fluid, in Pascals
        temperature: temperature of the fluid, in Kelvin
    
    Output: density of the gas
    """
    RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    RP.SETPATHdll(os.environ['RPPREFIX'])
    MASS_BASE_SI = RP.GETENUMdll(0,"MASS BASE SI").iEnum
    r = RP.REFPROPdll(fluid,"TP","ISENK",MASS_BASE_SI, 0,0,temperature, p_pa , [1.0])
    return r.Output[0]

def fluid_R_from_P_T(fluid, p_pa, temperature):
    """
    Inputs:
        fluid: string of fluid to analyze
        p_pa: pressure of the fluid, in Pascals
        temperature: temperature of the fluid, in Kelvin
    
    Output: specific gas constant (J / kg K)
    """
    RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    RP.SETPATHdll(os.environ['RPPREFIX'])
    MASS_BASE_SI = RP.GETENUMdll(0,"MASS BASE SI").iEnum
    r = RP.REFPROPdll(fluid,"TP","R",MASS_BASE_SI, 0,0,temperature, p_pa, [1.0])
    return r.Output[0]

def fluid_reynolds_from_P_T(fluid, p_pa, temperature, velocity, tube_diam):
    """
    Inputs:
        fluid: string of fluid to analyze
        p_pa: pressure of the fluid, in Pascals
        temperature: temperature of the fluid, in Kelvin
        velocity: velocity of gas in tube, in m/s
    
    Output: Reynolds number
    """
    RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
    RP.SETPATHdll(os.environ['RPPREFIX'])
    MASS_BASE_SI = RP.GETENUMdll(0,"MASS BASE SI").iEnum
    vis = RP.REFPROPdll(fluid,"TP","VIS",MASS_BASE_SI, 0,0,temperature, p_pa , [1.0]).Output[0]
    reyn = velocity * tube_diam / vis
    return reyn

def convert_psi_to_pa(p_in_psi):
    # source: google
    return p_in_psi*6894.76

