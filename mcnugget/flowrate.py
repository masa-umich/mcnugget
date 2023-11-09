import synnax as sy
import numpy as np
import matplotlib.pyplot as plt
from mcnugget.query import read
from mcnugget.time import elapsed_seconds

TR = sy.TimeRange(1678042983002521300, 1678042991250027500)

# 3/5 Test #s and Times
TR1 = sy.TimeRange(1678042983002521300, 1678042991250027500)
TR2 = sy.TimeRange(1678045281618912800, 1678045291301232600)
TR3 = sy.TimeRange(1678046637196518100, 1678046646645440300)
TR4 = sy.TimeRange(1678049505197942800, 1678049514237374500)


def flow_rate(
    DP: np.array[float],
    inlet_diam: float,
    throat_diam: float,
    rho: float,
    beta: float,
    C: float,
) -> np.array[float]:
    m_dots_1 = (
        (C * np.pi * (throat_diam**2) * ((2 * DP_edit * rho) ** 0.5))
        / (4 * ((1 - (beta**4)) ** 0.5))
    ) / 2.20462
    v_1 = np.sqrt((2 * DP_edit) / (rho * ((inlet_diam / throat_diam) ** 2 - 1)))
    m_1 = rho * v_1 * np.pi * throat_diam**2 / 4
    return rho * inlet_diam * v_1 / (2.73e-5)


if __name__ == "__main__":
    DATA = read(TR, "gse.pressure[15]", "Time")
    Time = elapsed_seconds(DATA["Time"])
    DP_raw = DATA["gse.pressure[15]"]  # psi * 10
    DP_edit = (DP_raw / 10) * 6894.76  # converting 10*psi to Pa

    C = 0.995  # discharge coefficient
    inlet_diam = 0.92  # in. (measured ID of the inlet)
    throat_diam = 0.79  # in. (both copied from flowmeter mastersheet
    rho = 8.34  # lb/ft^3
    beta = throat_diam / inlet_diam  # diameter ratio (<1)

    re_1 = flow_rate(DP_edit, inlet_diam, throat_diam, rho, beta, C)
    plt.plot(Time, re_1)
    plt.show()
