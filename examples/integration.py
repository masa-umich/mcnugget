import numpy as np
import matplotlib.pyplot as plt
from mcnugget.client import client

# We're going to fetch a named range from the server. This range represents a test we
# ran on october 28th to test Gooster. If you don't know what the name of your range is,
# use the Synnax console to find it.
rng = client.split_ranges.retrieve("October 28 Gooster")

# This channel contains our 2K bottle pressure for the range.
bottle_pressure = rng.gse_pressure_20

# This channel contains the timestamps recorded by the GSE DAQ.
time = rng.gse_time

# Offset the pressure by its mean.
adj_pressure = bottle_pressure - np.mean(bottle_pressure)

# Integrate the pressure curve
integrated = np.trapz(adj_pressure, time)

# Plot the data
plt.plot(time, adj_pressure)

# Set the labels
plt.xlabel("Time (ns)")
plt.ylabel("Pressure (psi)")

# Highlight the area under the curve
plt.fill_between(time, adj_pressure, alpha=0.5)

plt.annotate("Area: {:.2f}".format(integrated), xy=(0.5, 0.8), xycoords="axes fraction")

# Show the plot
plt.show()
