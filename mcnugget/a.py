import synnax
from mcnugget.query import read
import matplotlib.pyplot as plt

TR = synnax.TimeRange(1677605562912998100, 1677605905413741600)

DATA = read(TR, "ec.pressure[12]", "Time")

plt.plot(DATA["Time"], DATA["ec.pressure[12]"])

plt.show()




