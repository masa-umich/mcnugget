import synnax as sy

import numpy as np
import matplotlib.pyplot as plt

from mcnugget.query import read
from mcnugget.tests import VALVE_TIMINGS
from mcnugget.time import elapsed_seconds

def calculate_valve_timing(
        tr: sy.TimeRange,
        valve: str,
        pt: str,
        time: str = "Time"
):
    """
    Calculates the valve timing for a given valve and pressure transducer.

    Args:
        tr (sy.TimeRange): The time range to query.

    """

    data = read(tr, valve, pt, time)
    time_d = elapsed_seconds(data[time].to_numpy())

    # find the leading edge when the valve goes from 0 to 1
    valve_leading_edge = time_d[np.where(np.diff(data[valve].to_numpy()) == 1)][0]
    # find the point where the pressure first goes above 10
    pt_leading_edge = time_d[np.where(data[pt].to_numpy() > 1)][0]

    plt.axvline(valve_leading_edge, color="red")
    plt.axvline(pt_leading_edge, color="blue")

    plt.plot(time_d, data[pt].to_numpy())
    plt.ylabel("Pressure (psi)")
    plt.twinx()
    plt.plot(time_d, data[valve].to_numpy(), color="orange")
    plt.xlabel("Elapsed Time (s)")
    plt.ylabel("Valve State")
    plt.title(f"Timing 1: {pt_leading_edge - valve_leading_edge:.3f} s")
    plt.show()

if __name__ == "__main__":
    calculate_valve_timing(
        sy.TimeRange(1681142937035672000, 1681142937470433500),
        "ec.vlv7.en (hs)",
        "ec.pressure[12] (hs)",
        "Time (hs)"
    )
