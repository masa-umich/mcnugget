import matplotlib.pyplot as plt
from mcnugget.query import read_during_state, ECStates
from mcnugget.tests import TPC
from mcnugget.time import elapsed_seconds

# tr defines the time range we're interested in reading. An easy way to figure this
# out is to use the visualiation UI to copy the range (http://docs.synnaxlabs.com/visualize/select-a-range).
# In this case we're interested in the thermocouples while pressuring the COPV for a TPC test.
tr = TPC["02-25-23-01"]

CH_1 = "ec.tc[1]"
CH_2 = "ec.tc[2]"
CH_3 = "ec.tc[3]"
CH_4 = "ec.tc[4]"
TIME = "Time"

# Read the data from the specified channels when (ec.STATE) is in MANUAL.
# This makes sure we're only plotting data from during press and not the test.
# Note: this is the default state, so we don't really need to specify it.
data = read_during_state(tr, CH_1, CH_2, CH_3, CH_4, TIME, state=ECStates.MANUAL)

data_1 = data[CH_1].to_numpy()
data_2 = data[CH_2].to_numpy()
data_3 = data[CH_3].to_numpy()
data_4 = data[CH_4].to_numpy()

avg = (data_1 + data_2 + data_3 + data_4) / 4

plt.plot(elapsed_seconds(data[TIME].to_numpy()), avg)

plt.xlabel("Elapsed Time (s)")
plt.ylabel("Average Temperature (K)")

plt.show()
