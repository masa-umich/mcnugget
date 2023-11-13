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
pt1_data = read(TR, pt1, "Time")
pt2_data = read(TR, pt2, "Time")
tc1_data = read(TR, tc1, "Time")
tc2_data = read(TR, tc2, "Time")

# Set time variables
static_time = elapsed_seconds(pt1_data["Static Time"])
# stagnation_time = elapsed_seconds(stagnation_pdata["Stagnation Time"])

# Set pressure variables
static_pressure = pt1_data[pt1] * 6894.76  # PSI to Pa
stagnation_pressure = pt2_data[pt2] * 6894.76  # PSI to Pa

# Set temperature variables
static_temp = tc1_data[tc1]  # Kelvin
stagnation_temp = tc2_data[tc2]  # Kelvin

gamma = 1.4  # Specific heat
R = 296.8  # For Nitrogen, J/kg*K
A = 1  # CHANGE THIS
