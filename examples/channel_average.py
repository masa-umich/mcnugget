import synnax as sy 
import matplotlib.pyplot as plt
from mcnugget.query import read_during_state, ECStates

# tr defines the time range we're interested in reading. An easy way to figure this
# out is to use the visualiation UI to copy the range (http://docs.synnaxlabs.com/visualize/select-a-range).
tr = sy.TimeRange(0, 10)

CH_1 = "ec.pressure[7] (psi)"
CH_2 = "ec.pressure[8] (psi)"
CH_3 = "ec.pressure[9] (psi)"
CH_4 = "ec.pressure[10] (psi)"
TIME = "Time"

# Read the data from the specified channels when (ec.STATE) is in HOTFIRE.
# This makes sure we're only plotting data from during the test.
# Note: this is the default state, so we don't really need to specify it.
data = read_during_state(tr, CH_1, CH_2, CH_3, CH_4, TIME, state=ECStates.HOTFIRE)

data_1 = data[CH_1].to_numpy()
data_2 = data[CH_2].to_numpy()
data_3 = data[CH_3].to_numpy()
data_4 = data[CH_4].to_numpy()

avg = (data_1 + data_2 + data_3 + data_4) / 4

plt.plot(data[TIME].to_numpy(), avg)

plt.xlabel("Time (ns)")
plt.ylabel("Average Pressure (psi)")

plt.show()
