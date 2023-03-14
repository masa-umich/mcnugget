import numpy as np

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
# We'll integrate under this pressure curve.
PT_CH = "ec.pressure[9]"

# Read the data from the specified channels when (ec.STATE) is in HOTFIRE.
# This makes sure we're only plotting data from during the test.
# Note: this is the default state, so we don't really need to specify it.
data = read_during_state(tr, TIME_CH, PT_CH, state=ECStates.HOTFIRE)

# Pick out our timestamps
time = data[TIME_CH].to_numpy()
# Pick out our pressure data
pressure = data[PT_CH].to_numpy()
# Get the mean
pressure = pressure - np.mean(pressure)

# Integrate the pressure curve
integrated = np.trapz(pressure, time)

# Plot the data
plt.plot(time, pressure)

# Set the labels
plt.xlabel("Time (ns)")
plt.ylabel("Pressure (psi)")

# Highlight the area under the curve
plt.fill_between(time, pressure, alpha=0.5)

plt.annotate("Area: {:.2f}".format(integrated), xy=(0.5, 0.8), xycoords="axes fraction")

# Show the plot
plt.show()

