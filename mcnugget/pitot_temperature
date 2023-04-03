import synnax as sy
from mcnugget.query import read 
from mcnugget.time import elapsed_seconds
import numpy as np
import matplotlib.pyplot as plt
TR = sy.TimeRange(1678042983002521300, 1678042991250027500)

### NOTE TO CHANGE THE AREA VARIABLE BELOW

# Channel names and numbers
pt1 = "gse.pressure[15]"
pt2 = "gse.pressure[16]"
tc1 = "ec.tc[1]"
tc2 = "ec.tc[2]"

# Read in Data
static_pdata = read(TR,pt1, "Time")
stagnation_pdata = read(TR,pt2, "Time")
static_tdata = read(TR,tc1, "Time")
stagnation_tdata = read(TR,tc2, "Time")

# Set time variables
static_time = elapsed_seconds(static_pdata["Static Time"])
stagnation_time = elapsed_seconds(stagnation_pdata["Stagnation Time"])

# Set pressure variables
static_pressure = static_pdata[pt1] * 6894.76 #PSI to Pa
stagnation_pressure = stagnation_pdata[pt2]  * 6894.76 #PSI to Pa

# Set temperature variables
static_temp = static_tdata[tc1] #Kelvin
stagnation_temp = stagnation_tdata[tc2] #Kelvin

gamma = 1.4 # Specific heat
R = 296.8 # For Nitrogen, J/kg*K
A = 1 # CHANGE THIS
temp_ratio = stagnation_temp / static_temp # Calculate stagnation to static pressure ratio

# Calculate Mach number
M = (temp_ratio-1)*(2/(gamma-1))

calc_stag_P = static_pressure*((1+((gamma-1)/2)*M**2)**(gamma/(gamma-1)))

# Calculate Mass Flow Rate
letters = (1+((gamma-1)/2)*(M**2))**((gamma+1)/(2-2*gamma))
m_dot = (calc_stag_P/(np.sqrt(R*stagnation_temp)))*A*np.sqrt(gamma)*M*letters



