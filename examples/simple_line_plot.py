import synnax as sy
import matplotlib.pyplot as plt
from mcnugget.query import read_during_state, ECStates
from mcnugget.tests import TPC

# tr defines the time range we're interested in reading. An easy way to figure this
# out is to use the visualiation UI to copy the range (http://docs.synnaxlabs.com/visualize/select-a-range).
# In this case we're interested in the tank pressure during a TPC test.
tr = TPC["02-19-23-02"]

# This channel contains the timestamps for the data.
TIME_CH = "Time"
# This channel contains the pressure data we're interested in plotting.
PT_CH = "ec.pressure[9]"

# Read the data from the specified channels when (ec.STATE) is in MANUAL.
# If we wanted to read data during a test, we could switch this to ECStates.HOTFIRE.
data = read_during_state(tr, TIME_CH, PT_CH, state=ECStates.HOTFIRE)
# Pick out our timestamps
time = data[TIME_CH].to_numpy()
# Pick out our pressure data
pressure = data[PT_CH].to_numpy()

# Plot the data
plt.plot(time, pressure)

# Set the labels
plt.xlabel("Time (ns)")
plt.ylabel("Pressure (psi)")

# Show the plot
plt.show()


