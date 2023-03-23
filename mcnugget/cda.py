import synnax
from mcnugget.query import read 
from mcnugget.time import elapsed_seconds
import numpy as np
import matplotlib.pyplot as plt
TR = synnax.TimeRange(1677605689782918700, 1677605754433342200)
DATA = read(TR,"ec.pressure[12]", "Time")

Time = elapsed_seconds(DATA["Time"])
Pressures = DATA["ec.pressure[12]"]

R = 296.8
T = 280
GAMMA = 1.4
V = 0.01
m = (Pressures*V)/(R*T)
mdot = np.gradient(Pressures, Time)

term1 = sqrt(GAMMA) * Pressures /sqrt(T*R)
TERM2 = (0.5*(GAMMA+1)) ** (0.5*(-GAMMA - 1) /(GAMMA-1))

cda = mdot / term1 / term2
plt.plot(Time, cda*1550)
plt.xlabel("peepeepoopoo (time)")
plt.ylabel("pppp")
plt.show()











