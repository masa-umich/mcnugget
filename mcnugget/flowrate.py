import synnax
from mcnugget.query import read 
from mcnugget.time import elapsed_seconds
import numpy as np
import matplotlib.pyplot as plt
TR = synnax.TimeRange(1677367954335752200, 1677367959746683000)



# Read in Data
DATA = read(TR,"ec.pressure[7]", "Time")

# Set Variables for Pressure (also convert it to Pa) and Time
Time = elapsed_seconds(DATA["Time"])
DP = DATA["ec.pressure[7]"] * 6895

C = 0.995      #discharge coefficient
inlet_diam = 0.92     # in. (measured ID of the inlet)
throat_diam = 0.79     # in. (both copied from flowmeter mastersheet
rho = 8.34             # lb/ft^3
beta = throat_diam/inlet_diam  # diameter ratio (<1)

m_dots = ((C*np.pi*(throat_diam**2)*((2*DP*rho)**0.5))/(4*((1-(beta**4))**0.5)))/2.20462

plt.plot(Time, m_dots)
print(m_dots)
plt.show()















