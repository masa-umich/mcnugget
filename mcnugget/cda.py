import synnax
from mcnugget.query import read 
from mcnugget.time import elapsed_seconds
import numpy as np
import matplotlib.pyplot as plt
TR = synnax.TimeRange(1677605739099293700, 1677605759803447000)
#TR.start = TR.start+synnax.TimeSpan.HOUR
#TR.end = TR.end+synnax.TimeSpan.HOUR

# Read in Data
DATA = read(TR,"ec.pressure[12]", "Time")

# Set Variables for Pressure (also convert it to Pa) and Time
Time = elapsed_seconds(DATA["Time"])
Pressures = DATA["ec.pressure[12]"] * 6895

# Set Vars for m dot and cda equations
R = 296.8
T = 280
GAMMA = 1.4
V = 0.01

# Mass in the tank
m = (Pressures*V)/(R*T)
# calc mdot going out of the tank
mdot = np.gradient(m, Time)

# Eqns from NASA paper on mdot equation, with terms split up
TERM1 = (np.sqrt(GAMMA) * Pressures) /np.sqrt(T*R)
TERM2 = (0.5*(GAMMA+1)) ** (0.5*(-GAMMA - 1) /(GAMMA-1))

# CdA established
cda = -mdot / (TERM1 * TERM2)

# Begin Plotting + labelling
plt.plot(Time, cda*1550)
plt.ylabel("CdA (in^2)")
plt.title("Cda over Time :)")
plt.twinx()
plt.plot(Time, Pressures)
#plt.plot(Time,mdot)
#plt.xlabel("Time (S)")
#plt.ylabel("Pressure (Pa)")

# Find and print avg cda
avg_cda = np.mean(cda*1550)
print("Average CdA is", avg_cda)

# Est. radius from avg cda and assumed Cd.
cd = 0.7
a = avg_cda/cd
r = (a/np.pi)**0.5
print("radius is ", r)

plt.savefig("biggiechungus_cda_plot")

plt.show()










