"""

### OVERVIEW ###

This autosequence opens the OX REG and FUEL REG to release high-pressure gas

1. Set starting state
    - Energize all normally_open
    - De-energize all normally_closed

2. Confirm tank pressures are nominal
    - use FUEL_PRE_PRESS to pressurize the FUEL tank to TARGET_1 if necessary
    - use OX_PRE_PRESS to pressurize the OX tank to TARGET_2 if necessary
    - continue once both tank pressures are nominal

3. Open Valves
    - The following need to be opened at the same time:
        - FUEl_PREVALVE
        - OX_PREVALVE
        - FUEL_PRESS_ISO
        - OX_PRESS_ISO
        - OX_DOME_ISO
    - We will then wait for 25 seconds, barring an abort

4. Close Valves
    - Close all the valves opened in step 3
    - Open FUEL_VENT and OX_LOW_FLOW_VENT

X. Abort
    - The only conditions which will trigger an abort:
        - 2/3 PTs reading above maximum pressure for OX_TANK or FUEL_TANK
        - Manual ctrl-c

"""

import syauto
import time
from synnax.control.controller import Controller
import synnax as sy
import statistics
from collections import deque

# this connects to the synnax simulation server
client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

# Connects to masa cluster
# client = sy.Synnax(
#     host="synnax.masa.engin.umich.edu",
#     port=80,
#     username="synnax",
#     password="seldon",
#     secure=True
# )

# TODO check sop for these
FUEL_PT_1 = ""
FUEL_PT_2 = ""
FUEL_PT_3 = ""
OX_PT_1 = ""
OX_PT_2 = ""
OX_PT_3 = ""

OX_FIRE = True
FUEL_FIRE = True
# change these to trigger a fuel-only or ox-only fire

#TODO fill these in
FUEL_TARGET_PRESSURE = 0
OX_TARGET_PRESSURE = 0

FUEL_PRESSURE_INCREMENT = 0
OX_PRESSURE_INCREMENT = 0

FUEL_PRESSURE_MAX = 0
OX_PRESSURE_MAX = 0

# TODO check sop for these
fuel_prevalve_cmd = ""
fuel_prevalve_ack = ""

ox_prevalve_cmd = ""
ox_prevalve_ack = ""

fuel_press_iso_cmd = ""
fuel_press_iso_ack = ""

ox_press_iso_cmd = ""
ox_press_iso_ack = ""

ox_dome_iso_cmd = ""
ox_dome_iso_ack = ""

fuel_vent_cmd = ""
fuel_vent_ack = ""

ox_low_flow_vent_cmd = ""
ox_low_flow_vent_ack = ""

ACKS = [fuel_prevalve_ack, ox_prevalve_ack, fuel_press_iso_ack, ox_press_iso_ack, ox_dome_iso_ack, fuel_vent_ack, ox_low_flow_vent_ack]
CMDS = [fuel_prevalve_cmd, ox_prevalve_cmd, fuel_press_iso_cmd, ox_press_iso_cmd, ox_dome_iso_cmd, fuel_vent_cmd, ox_low_flow_vent_cmd]
PTS = [FUEL_PT_1, FUEL_PT_2, FUEL_PT_3, OX_PT_1, OX_PT_2, OX_PT_3]

# This section implements a running average for the PT sensors to mitigate the effects of noise
FUEL_PT_1_DEQUE = deque()
FUEL_PT_2_DEQUE = deque()
FUEL_PT_3_DEQUE = deque()
OX_PT_1_DEQUE = deque()
OX_PT_2_DEQUE = deque()
OX_PT_3_DEQUE = deque()
FUEL_PT_1_SUM = 0
FUEL_PT_2_SUM = 0
FUEL_PT_3_SUM = 0
OX_PT_1_SUM = 0
OX_PT_2_SUM = 0
OX_PT_3_SUM = 0

AVG_DICT = {
    FUEL_PT_1: FUEL_PT_1_DEQUE,
    FUEL_PT_2: FUEL_PT_2_DEQUE,
    FUEL_PT_3: FUEL_PT_3_DEQUE,
    OX_PT_1: OX_PT_1_DEQUE,
    OX_PT_2: OX_PT_2_DEQUE,
    OX_PT_3: OX_PT_3_DEQUE
}

SUM_DICT = {
    FUEL_PT_1: FUEL_PT_1_SUM,
    FUEL_PT_2: FUEL_PT_2_SUM,
    FUEL_PT_3: FUEL_PT_3_SUM,
    OX_PT_1: OX_PT_1_SUM,
    OX_PT_2: OX_PT_2_SUM,
    OX_PT_3: OX_PT_3_SUM
}

RUNNING_AVERAGE_LENGTH = 20
# for 200Hz data, this correlates to an average over 0.1 seconds

def get_averages(auto: Controller, read_channels: list[str]) -> dict[str, float]:
    # this function takes in a list of channels to read from, 
    # and returns a dictionary with the average for each - {channel: average}
    averages = {}
    for channel in read_channels:
        AVG_DICT[channel].append(auto[channel])  # adds the new data to the deque
        SUM_DICT[channel] += auto[channel]  # updates running total
        if len(AVG_DICT[channel]) > RUNNING_AVERAGE_LENGTH:
            SUM_DICT[channel] -= AVG_DICT[channel].popleft()  # updates running total and removes elt
        averages[channel] = SUM_DICT[channel] / len(AVG_DICT[channel])  # adds mean to return dictionary
    return averages


with client.control.acquire("Reg Fire", ACKS + PTS, CMDS, 200) as auto:
    try:
        fuel_prevalve = syauto.Valve(auto=auto, cmd=fuel_prevalve_cmd, ack=fuel_prevalve_ack, normally_open=False)
        # TODO create other valves

        # TODO write sequence

        # TODO safe system

    except KeyboardInterrupt as e:
        # TODO abort case 
        print("Manual abort, safing system")
