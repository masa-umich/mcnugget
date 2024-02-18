""""
This is the prototype of the hotfire autosequence.
Currently, it does the following (edit if changed)
1. TODO: safes system
2. TODO: pressurizes accumulator press and L-stand
3. TODO: runs TPC to maintain L-stand pressure

- The TPC function opens/closes TESCOMS 1-4 automatically to maintain pressure
- It does this based on the pressure in the L-stand
    - Uses valve 1 to keep pressure between BOUND_1 and TARGET_1
    - Uses valve 2 to keep pressure between BOUND_2 and TARGET_2
    - same for 3 and 4

If you ABORT this script (by pressing ctrl-c while it is running), it will
    - TODO: impelment this
    - close accumulator valve
    - close all tescoms
    - open MPV
    - open MPV vent
"""

import time
import synnax as sy
from synnax.control.controller import Controller
import syauto
# from typing import list

ISO_PRESS = "iso press channel here"

TPC_PRESS = ISO_PRESS


'''
This function opens and closes the four valves specified to maintain pressure
FOUR THRESHOLDS produce FIVE REGIONS which trigger different actions

    - ABOVE threshold 1
        1-closed, 2-closed, 3-closed, 4-closed

    - ABOVE threshold 2 but BELOW threshold 1
        1-open, 2-closed, 3-closed, 4-closed

    - ABOVE threshold 3 but BELOW threshold 2
        1-open, 2-open, 3-closed, 4-closed

    - ABOVE threshold 4 but BELOW threshold 3
        1-open, 2-open, 3-open, 4-closed

    - BELOW threshold 4
        1-open, 2-open, 3-open, 4-open

This means valves are opening or closing to keep the pressure between T1 and T2, 
then between T2 and T3, between T3 and T4, and so on.
'''
def run_tpc(auto: Controller, valves: list[syauto.Valve], thresholds: list[float], press_chan: str):

    v1 = valves[0]
    v2 = valves[1]
    v3 = valves[2]
    v4 = valves[3]

    t1 = thresholds[0]
    t2 = thresholds[1]
    t3 = thresholds[2]
    t4 = thresholds[3]

    pressure = auto[press_chan]

    if pressure > t1:
        syauto.open_close_many_valves(auto, [], [v1, v2, v3, v4])
        # closes 1-4

    elif pressure < t1 and pressure > t2:
        syauto.open_close_many_valves(auto, [v1], [v2, v3, v4])
        # opens 1, closes 2-4

    elif pressure < t2 and pressure > t3:
        syauto.open_close_many_valves(auto, [v1, v2], [v3, v4])
        # opens 1-2, closes 3-4

    elif pressure < t3 and pressure > t4:
        syauto.open_close_many_valves(auto, [v1, v2, v3], [v4])
        # opens 1-3, closes 4

    elif pressure < t4:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])
        # opens 1-4

    return pressure < 15
