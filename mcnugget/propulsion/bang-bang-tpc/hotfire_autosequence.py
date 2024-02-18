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
There are FOUR THRESHOLDS which trigger different actions

    - if the pressure rises above threshold 1, valves 1-4 (all valves) will close
    - if the pressure rises above threshold 2, valves 2-4 will close
    - if the pressure rises above threshold 3, valves 3-4 will close
    - if the pressure rises above threshold 4, valve 4 will close

    - if the pressure falls below threshold 1, valve 1 will open
    - if the pressure falls below threshold 2, valve 1-2 will open
    - if the pressure falls below threshold 3, valve 1-3 will open
    - if the pressure falls below threshold 4, valve 1-4 will open

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
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])

    elif pressure > t2:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])

    elif pressure > t3:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])

    elif pressure > t4:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])


    if pressure < t1:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])

    elif pressure < t2:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])

    elif pressure < t3:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])

    elif pressure < t4:
        syauto.open_close_many_valves(auto, [v1, v2, v3, v4], [])

    # if the pressure drops below 15, the tanks are mostly empty and the test is finished
    return pressure < 15
