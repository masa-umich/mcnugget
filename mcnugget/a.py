import synnax
from mcnugget.query import read
import matplotlib.pyplot as plt

TR = synnax.TimeRange(1677605739099293700, 1677605759803447000)

DATA = read(TR, "ec.pressure[12]", "Time")

plt.plot(DATA["Time"], DATA["ec.pressure[12]"])

plt.show()




