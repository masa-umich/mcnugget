import matplotlib.pyplot as plt
import synnax as sy
from mcnugget.client import client

# We're going to fetch a named range from the server. This range represents a test we
# ran on october 28th to test Gooster. If you don't know what the name of your range is,
# use the Synnax console to find it.
rng = client.split_ranges.retrieve("October 28 Gooster")

# This channel contains our 2K bottle pressure for the range.
bottle_pressure = rng.gse_pressure_20

# Converts our timestamps to elapsed seconds since the start of the range.
elapsed_time = sy.elapsed_seconds(rng.gse_time)

# Plot the data
plt.plot(elapsed_time, bottle_pressure)

# Set the labels
plt.xlabel("Time (s)")
plt.ylabel("Pressure (psi)")

# Show the plot
plt.show()
