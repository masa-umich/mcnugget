import matplotlib.pyplot as plt
import numpy as np
import math
import scipy
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import os
import refprop_functions as refprop

# https://refprop-docs.readthedocs.io/en/latest/DLL/high_level.html#f/_/REFPROPdll


# created by Ichiro Ausin
# Place to store functions for refprop

# If the RPPREFIX environment variable is not already set by your installer (e.g., on windows), 
# then uncomment this line and set the absolute path to the location of your install of 
# REFPROP

def find_friction_factor(relative_roughness, reyn_num):
	f_old = 0.02
	diff = 1
	while diff > 0.001:
		f_new = (2 * math.log10((relative_roughness/3.7) +(2.51/(reyn_num*math.sqrt(f_old))) ))**(-2)
		diff = np.abs(f_new-f_old)
		f_old = f_new
	
	
	return f_new














