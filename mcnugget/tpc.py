import matplotlib.pyplot as plt

import numpy as np
import synnax as sy
from mcnugget.query import read_during_state, ECStates
from mcnugget.tests import TPC
from mcnugget.time import elapsed_seconds

def analyze_tpc(
    tr: sy.TimeRange,
    target: float = 100,
    upper: float = 110,
    lower: float = 90,
    prop_press: str = "ec.pressure[7] (psi)",
    time: str = "Time",
    ):
    """Perform basic high level analysis of a TPC (Tank Pressure Control) test."""
    data = read_during_state(
        tr
        prop_press,
        time,
        state=ECStates.HOTFIRE
    )
    time_d = elapsed_seconds(data[time].to_numpy())
    prop_press_d = data[prop_press].to_numpy()
    prop_max, prop_min = np.max(prop_press_d), np.min(prop_press_d)

    plt.plot(time_d, prop_press_d)
    plt.xlabel("Time (s)")
    plt.ylabel("Pressure (psi)")

    plt.annotate(f"Max: {prop_max:.2f} psi", (0.5, 0.9), xycoords="axes fraction")
    plt.annotate(f"Min: {prop_min:.2f} psi", (0.5, 0.85), xycoords="axes fraction")

    plt.axhline(target, color="r", linestyle="--")
    plt.axhline(upper, color="r", linestyle="--")
    plt.axhline(lower, color="r", linestyle="--")

    plt.show()    

if __name__ == "__main__":
    analyze_tpc(
        tr=sy.TimeRange(1670197424106298000, 1670197430643991800),
        target = 280,
        upper=330,
        lower=250
    )

