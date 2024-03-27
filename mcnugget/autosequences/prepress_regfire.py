"""

### OVERVIEW ###

This autosequence combines the processes of pre_press.py and reg_fire.py.

When pre_press is true:
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
        - Open FUEL_VENT and OX_LOW_FLOW_VENT and PRESS_VENT

    X. Abort
        - The only conditions which will trigger an abort:
            - 2/3 PTs reading above maximum pressure for OX_TANK or FUEL_TANK
            - Manual ctrl-c

When reg_fire is true:
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
    - Open FUEL_VENT and OX_LOW_FLOW_VENT and PRESS_VENT

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

REG_FUEL_FIRE = False

REG_OX_FIRE = False

PRE_PRESS = False

REGFIRE_PREPRESS = False

# change names and numbers to match the actual channels
# valve names to channel names
FUEL_PRE_PRESS_ACK = "gse_doa_9"
FUEL_PRE_PRESS_CMD = "gse_doc_9"
FUEL_VENT_ACK = "gse_doa_15"
FUEL_VENT_CMD = "gse_doc_15"
OX_PRE_PRESS_ACK = "gse_doa_10"
OX_PRE_PRESS_CMD = "gse_doc_10"
OX_LOW_FLOW_VENT_ACK = "gse_doa_16"
OX_LOW_FLOW_VENT_CMD = "gse_doc_16"
FUEL_PT_1 = "gse_ai_3"
FUEL_PT_2 = "gse_ai_4"
FUEL_PT_3 = "gse_ai_35"
OX_PT_1 = "gse_ai_6"
OX_PT_2 = "gse_ai_7"
OX_PT_3 = "gse_ai_8"
PRESS_VENT_CMD = "gse_doc_18"
PRESS_VENT_ACK = "gse_doa_18"
OX_PREVALVE_CMD = "gse_doc_21"
OX_PREVALVE_ACK = "gse_doa_21"
FUEL_PREVALVE_CMD = "gse_doc_22"
FUEL_PREVALVE_ACK = "gse_doa_22"
FUEL_PRESS_ISO_CMD = "gse_doc_2"
FUEL_PRESS_ISO_ACK = "gse_doa_2"
OX_PRESS_ISO_CMD = "gse_doc_1"
OX_PRESS_ISO_ACK = "gse_doa_1"
OX_DOME_ISO_CMD = "gse_doc_3"
OX_DOME_ISO_ACK = "gse_doa_3"

PTS = [FUEL_PT_1, FUEL_PT_2, FUEL_PT_3, OX_PT_1, OX_PT_2, OX_PT_3]
ACKS = [FUEL_PREVALVE_ACK, OX_PREVALVE_ACK, FUEL_PRESS_ISO_ACK, OX_PRESS_ISO_ACK, OX_DOME_ISO_ACK, FUEL_VENT_ACK, OX_LOW_FLOW_VENT_ACK, PRESS_VENT_ACK, FUEL_PRE_PRESS_ACK, OX_PRE_PRESS_ACK]
CMDS = [FUEL_PREVALVE_CMD, OX_PREVALVE_CMD, FUEL_PRESS_ISO_CMD, OX_PRESS_ISO_CMD, OX_DOME_ISO_CMD, FUEL_VENT_CMD, OX_LOW_FLOW_VENT_CMD, PRESS_VENT_CMD, FUEL_PRE_PRESS_CMD, OX_PRE_PRESS_CMD]

# List of channels we're going to read from and write to
WRITE_TO = []
READ_FROM = []
WRITE_TO.append(cmd_chan for cmd_chan in CMDS)
READ_FROM.append(ack_chan for ack_chan in ACKS)
READ_FROM.append(PT_chan for PT_chan in PTS)

# TODO: update these before running the autosequence

TARGET_FUEL_PRESSURE = 453
UPPER_FUEL_PRESSURE = TARGET_FUEL_PRESSURE + 20
LOWER_FUEL_PRESSURE = TARGET_FUEL_PRESSURE - 10
# UPPER_FINAL_FUEL_PRESSURE = 490  # FUEL TEST PRESSURE
# LOWER_FINAL_FUEL_PRESSURE = UPPER_FINAL_FUEL_PRESSURE - 20
MAX_FUEL_PRESSURE = 525

TARGET_OX_PRESSURE = 397
UPPER_OX_PRESSURE = TARGET_OX_PRESSURE + 20
LOWER_OX_PRESSURE = TARGET_OX_PRESSURE - 10
# UPPER_FINAL_OX_PRESSURE = 450  # OX REG SET PRESSURE
# LOWER_FINAL_OX_PRESSURE = UPPER_FINAL_OX_PRESSURE - 20
MAX_OX_PRESSURE = 525

RUNNING_AVERAGE_LENGTH = 5  # samples
# at 50Hz data, this means 0.1s


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

RUNNING_AVERAGE_LENGTH = 5
# for 50Hz data, this correlates to an average over 0.1 seconds

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


FIRE_DURATION = 25


with client.control.acquire("Pre Press + Reg Fire", READ_FROM, WRITE_TO, 200) as auto:
    fuel_prevalve = syauto.Valve(auto=auto, cmd=FUEL_PREVALVE_CMD, ack=FUEL_PREVALVE_ACK, normally_open=False)
    ox_prevalve = syauto.Valve(auto=auto, cmd=OX_PREVALVE_CMD, ack=OX_PREVALVE_ACK, normally_open=False)
    fuel_press_iso = syauto.Valve(auto=auto, cmd = FUEL_PRESS_ISO_CMD, ack = FUEL_PRESS_ISO_ACK, normally_open=False)
    ox_press_iso = syauto.Valve(auto=auto, cmd = OX_PRESS_ISO_CMD, ack = OX_PRESS_ISO_ACK, normally_open=False)
    ox_dome_iso = syauto.Valve(auto=auto, cmd = OX_DOME_ISO_CMD, ack = OX_DOME_ISO_ACK, normally_open=False)
    fuel_vent = syauto.Valve(auto=auto, cmd = FUEL_VENT_CMD, ack = FUEL_VENT_ACK, normally_open=True)
    ox_low_flow_vent = syauto.Valve(auto=auto, cmd = OX_LOW_FLOW_VENT_CMD, ack = OX_LOW_FLOW_VENT_ACK, normally_open=True)
    fuel_prepress = syauto.Valve(auto=auto, cmd = FUEL_PRE_PRESS_CMD, ack = FUEL_PRE_PRESS_ACK, normally_open=False)
    ox_prepress = syauto.Valve(auto=auto, cmd = OX_PRE_PRESS_CMD, ack = OX_PRE_PRESS_ACK, normally_open=False)
    press_vent = syauto.Valve(auto=auto, cmd = PRESS_VENT_CMD, ack = PRESS_VENT_ACK, normally_open=True)

    print("Setting starting state")
    syauto.close_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso, fuel_vent, ox_low_flow_vent, press_vent, ox_prepress, fuel_prepress])
    time.sleep(2)

    # abort functions
    def ox_abort(auto_: Controller):
        print("aborting ox tanks")
        syauto.close_all(auto_, [ox_prepress])
        input("Would you like to open ox low flow vent? y/n")
        if (input == "y"):
            syauto.open_all(auto_, [ox_low_flow_vent])
            print("ox_low_flow_vent safed")
        input("Press any key to continue pressing or ctrl+c to abort")


    def fuel_abort(auto_: Controller):
        print("aborting fuel tanks")
        syauto.close_all(auto_, [fuel_prepress])
        input("Would you like to open fuel vent? y/n")
        if (input == "y"):
            syauto.open_all(auto, [fuel_vent])
            print("fuel_vent safed")
        input("Press any key to continue pressing or ctrl+c to abort")

    def pressurized(auto: Controller) -> bool:
        averages = get_averages(auto, PTS)

        ox_average = statistics.median([averages[OX_PT_1], averages[OX_PT_2], averages[OX_PT_3]])
        ox_pre_press_open = auto[OX_PRE_PRESS_ACK]
        fuel_average = statistics.median([averages[FUEL_PT_1], averages[FUEL_PT_2], averages[FUEL_PT_3]])
        fuel_pre_press_open = auto[FUEL_PRE_PRESS_ACK]

        if REG_FUEL_FIRE:
            if fuel_pre_press_open and fuel_average >= UPPER_FUEL_PRESSURE:
                fuel_prepress.close()

            if not fuel_pre_press_open and fuel_average < LOWER_FUEL_PRESSURE:
                fuel_prepress.open()

            if fuel_pre_press_open and fuel_average > MAX_FUEL_PRESSURE:
                fuel_prepress.close()
                print("ABORTING FUEL due to high pressure")
                if REG_OX_FIRE:
                    if ox_pre_press_open and ox_average > MAX_OX_PRESSURE:
                        print("ABORTING OX due to high pressure")
                return True

        if REG_OX_FIRE:
            if ox_pre_press_open and ox_average >= UPPER_OX_PRESSURE:
                ox_prepress.close()

            if not ox_pre_press_open and ox_average < LOWER_OX_PRESSURE:
                ox_prepress.open()    

            if ox_pre_press_open and ox_average > MAX_OX_PRESSURE:
                print("ABORTING OX due to high pressure")
                ox_abort()
                return True

    # def over_pressurize(auto: Controller) -> bool:
    #     averages = get_averages(auto, PTS)

    #     ox_average = statistics.median([averages[OX_PT_1], averages[OX_PT_2], averages[OX_PT_3]])
    #     ox_pre_press_open = auto[OX_PRE_PRESS_ACK]
    #     fuel_average = statistics.median([averages[FUEL_PT_1], averages[FUEL_PT_2], averages[FUEL_PT_3]])
    #     fuel_pre_press_open = auto[FUEL_PRE_PRESS_ACK]

    #     if REG_FUEL_FIRE:
    #         if fuel_pre_press_open and fuel_average >= UPPER_FINAL_FUEL_PRESSURE:
    #             fuel_prepress.close()

    #         if not fuel_pre_press_open and fuel_average < LOWER_FINAL_FUEL_PRESSURE:
    #             fuel_prepress.open()

    #         if fuel_pre_press_open and fuel_average > MAX_FUEL_PRESSURE:
    #             fuel_prepress.close()
    #             print("ABORTING FUEL due to high pressure")
    #             if REG_OX_FIRE:
    #                 if ox_pre_press_open and ox_average > MAX_OX_PRESSURE:
    #                     print("ABORTING OX due to high pressure")
    #             return True

    #     if REG_OX_FIRE:
    #         if ox_pre_press_open and ox_average >= UPPER_FINAL_OX_PRESSURE:
    #             ox_prepress.close()

    #         if not ox_pre_press_open and ox_average < LOWER_FINAL_FUEL_PRESSURE:
    #             ox_prepress.open()    

    #         if ox_pre_press_open and ox_average > MAX_OX_PRESSURE:
    #             print("ABORTING OX due to high pressure")
    #             ox_abort()
    #             return True
        
    #    reg_fire_ready = not REG_FUEL_FIRE or (LOWER_FINAL_FUEL_PRESSURE < fuel_average and fuel_average < UPPER_FINAL_FUEL_PRESSURE)
    #    ox_fire_ready = not REG_OX_FIRE or (LOWER_FINAL_OX_PRESSURE < ox_average and ox_average < UPPER_FINAL_OX_PRESSURE)
    #    if reg_fire_ready and ox_fire_ready:
    #        return True
        

    def reg_fire():
        # auto.wait_until(over_pressurize)

        print("commencing fire")
        syauto.open_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso])
        time.sleep(FIRE_DURATION)
        syauto.open_close_many_valves(auto,[fuel_vent, ox_low_flow_vent, press_vent],[fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso])
        print("terminating fire")


    # this block runs the overall sequence
    try:
            start = sy.TimeStamp.now()
            time.sleep(1)

            print("pressurizing fuel and ox")
            auto.wait_until(pressurized)
            # the above statement will only finish if an abort is triggered

    except KeyboardInterrupt:
        syauto.close_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso, fuel_prepress, ox_prepress])
        answer = input("Valves are closed. Input `fire` to commence reg_fire portion of autosequence or anything else to skip")
        if answer == "fire":
            reg_fire()   

        ans = input("Aborting - would you like to open vents? y/n")
        if ans == "y":
            syauto.open_all(auto, [fuel_vent, ox_low_flow_vent, press_vent])

        # this creates a range in synnax so we can view the data
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Pre Press Coldflow Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )
