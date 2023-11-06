import synnax as sy
import matplotlib.pyplot as plt
from mcnugget.query import client


d = client.ranges.retrieve("October 28 Gooster")
plt.plot(d.gse_time, d.gse_pressure_20)
plt.show()