import numpy as np
import matplotlib.pyplot as plt
from mcnugget.query import read
from mcnugget.time import elapsed_seconds
import synnax as sy

AMBIENT_PRESSURE = 14.7


def mass_flow_rate(
    density: float,
    dp: np.array,
    cda: float,
):
    return cda * np.sqrt(2 * density * dp)


LOX_DOME_NAME = "ec.pressure[11] (hs)"
FUEL_MANIFOLD_NAME = "ec.pressure[12] (hs)"
REGEN_MANIFOLD_NAME = "ec.pressure[19] (hs)"
LOX_TANK_NAME = "ec.pressure[5] (hs)"
FUEL_TANK_NAME = "ec.pressure[9] (hs)"
LOX_MPV_NAME = "ec.vlv6.en (hs)"
FUEL_MPV_NAME = "ec.vlv7.en (hs)"
TIME_NAME = "Time (hs)"

# tr = sy.TimeRange(1681142937492482600, 1681142943980569600)
tr = sy.TimeRange(1681142937689518000, 1681142945217309700)

DATA = read(
    tr,
    LOX_DOME_NAME,
    LOX_TANK_NAME,
    TIME_NAME,
)

TIME_DATA = elapsed_seconds(DATA[TIME_NAME])

FUEL_DENSITY = 1000  # kg/m^3
LOX_DENSITY = 533.38  # kg/m^3

LOX_DOM = DATA[LOX_DOME_NAME] * 0.6 * 6894.75729
LOX_TANK_D = DATA[LOX_TANK_NAME] * 6894.75729

FUEL_CDA = 8.0475e-5
LOX_CDA = 0.000141
LOX_FEEDLINE_CDA = 6.74e-5

MASS_FLOW_RATE_INJ = mass_flow_rate(
    LOX_DENSITY,
    LOX_DOM,
    LOX_CDA,
)

MASS_FLOW_RATE_LINE = mass_flow_rate(
    LOX_DENSITY,
    LOX_TANK_D,
    LOX_FEEDLINE_CDA,
)

plt.plot(TIME_DATA, MASS_FLOW_RATE_INJ, label="Mass flow rate (kg/s)", color="red")
plt.plot(TIME_DATA, MASS_FLOW_RATE_LINE, label="Mass flow rate (kg/s)", color="orange")
plt.legend()

print(
    f"""
    "LOX dome: {DATA[LOX_DOME_NAME][0]}",
    "Lox tank: {DATA[LOX_TANK_NAME][0]}",
    "Injector Mass flow rate: {MASS_FLOW_RATE_INJ[0]}",
    "Feed line Mass flow rate: {MASS_FLOW_RATE_LINE[0]}",
"""
)

TOTAL_INJ = np.trapz(MASS_FLOW_RATE_INJ, TIME_DATA)
TOTAL_LINE = np.trapz(MASS_FLOW_RATE_LINE, TIME_DATA)

# add annotation
plt.annotate(
    f"Injector mass flow: {TOTAL_INJ:.2f} kg",
    xy=(0.25, 0.1),
    xycoords="axes fraction",
    horizontalalignment="center",
    bbox=dict(
        boxstyle="round",
        fc="w",
        ec="k",
        lw=1,
    ),
)

plt.annotate(
    f"Feed line mass flow: {TOTAL_LINE:.2f} kg",
    xy=(0.25, 0.05),
    xycoords="axes fraction",
    horizontalalignment="center",
    bbox=dict(
        boxstyle="round",
        fc="w",
        ec="k",
        lw=1,
    ),
)
plt.show()
