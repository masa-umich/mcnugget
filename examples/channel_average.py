import matplotlib.pyplot as plt
import numpy as np
import synnax as sy
from mcnugget.client import client

# We're going to fetch a named range from the server. This range represents a test we
# ran on october 28th to test Gooster. If you don't know what the name of your range is,
# use the Synnax console to find it.
rng = client.split_ranges.retrieve("October 28 Gooster")

time = sy.elapsed_seconds(rng.gse_time)

# get the vectorized average of the data using numpy
avg = np.average(
    [rng.gse_pressure_20, rng.gse_pressure_13, rng.gse_pressure_12], axis=0
)

plt.plot(time, avg)

plt.xlabel("Elapsed Time (s)")
plt.ylabel("Average Pressure (psi)")

plt.show()
