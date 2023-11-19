# Trevor's quick CdA calculator
#   Requires the following:
#   - Total pressure
#   - Temperature
#   - Flowrate in SCFM
#   Outputs:
#   - The CdA of your system's choke point (assuming that your measurements are upstream of it)
#   Problems for the future:
#   - Make it work with arrays of data (Only have single calc rn because flowmeter data wasn't timestamped and I figured working with max and min values would suffice)
import os
os.environ['RPPREFIX'] = r'C:/Program Files (x86)/REFPROP'

import numpy as np
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import pandas
import glob
import matplotlib.pyplot as plt

# Set up REFPROP library
RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
RP.SETPATHdll(os.environ['RPPREFIX'])
MOLAR_BASE_SI = RP.GETENUMdll(0, "MOLAR BASE SI").iEnum
MASS_BASE_SI = RP.GETENUMdll(0, "MASS BASE SI").iEnum

# Obtain input for flowrate in SCFM and get it into metric
flowrate = float(input("Enter flowrate in SCFM: "))
flowrate = (flowrate/60)*0.0283168 # This goes from SCFM to standard cubic meters per second

# Input fluid conditions for the given flowrate
P = float(input("Input total pressure in psi: "))
P = P*6894.76 # Psi to Pa
T = float(input("Input TC temp in K: "))

# Get densities and gamma from REFPROP and convert flowrate to kg/s
# - Flowmeter standardized to 100 psi at 70 deg. F
rho_actual = RP.REFPROPdll("NITROGEN","TP","D", MASS_BASE_SI,0,0,P,T,[1.0]).Output[0]
gamma = RP.REFPROPdll("NITROGEN","TP","CP/CV", MASS_BASE_SI,0,0,P,T,[1.0]).Output[0]
rho_standard = RP.REFPROPdll("NITROGEN","TP","D", MASS_BASE_SI,0,0,100*6894.76,294.261,[1.0]).Output[0]
flowrate = flowrate*rho_standard

# Calculate and output CdA
CdA = flowrate/(gamma*rho_actual*P*(2/(gamma+1))**((gamma+1)/(gamma-1)))**0.5
CdA = CdA*1550 # Convert from square meters to square inches
print (CdA)