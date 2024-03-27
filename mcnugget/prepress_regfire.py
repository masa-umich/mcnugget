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
# CHANGE THESE TO LOOPS
WRITE_TO = []
READ_FROM = []
for i in range(1, 25):
    WRITE_TO.append(f"gse_doc_{i}")
    READ_FROM.append(f"gse_doa_{i}")
for i in range(1, 37):
    READ_FROM.append(f"gse_ai_{i}")
for i in range(1, 17):
    READ_FROM.append(f"gse_tc_{i}")

start = sy.TimeStamp.now()
NOTIFIED = False

# TODO:
# PLEASE UPDATE/CONFIRM ALL VARIABLES BEFORE RUNNING TEST
# Pressures are in psi
FUEL_TARGET = 453
OX_TARGET = 397
UPPER_FUEL_PRESSURE = 473
LOWER_FUEL_PRESSURE = 423
MAX_FUEL_PRESSURE = 525
UPPER_OX_PRESSURE = 417
LOWER_OX_PRESSURE = 377
MAX_OX_PRESSURE = 525
# TODO: target + bound instead of upper/lower

RUNNING_AVERAGE_LENGTH = 20  # samples
# at 200Hz data, this means 0.1s


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



def reg_fuel_fire():
    NOMINAL_THRESHOLD = 20
    FIRE_DURATION = 25
    def fuel_pressurized(auto: Controller) -> bool:
        averages = get_averages(auto, PTS)
        fuel_average = statistics.median([averages[FUEL_PT_1], averages[FUEL_PT_2], averages[FUEL_PT_3]])
        fuel_pre_press_open = auto[FUEL_PRE_PRESS_ACK]

        if fuel_pre_press_open and fuel_average >= FUEL_TARGET:
            fuel_prepress.close()

        if not fuel_pre_press_open and fuel_average < FUEL_TARGET - NOMINAL_THRESHOLD:
            fuel_prepress.open()

        if fuel_pre_press_open and fuel_average > MAX_FUEL_PRESSURE:
            fuel_prepress.close()
            print("ABORTING FUEL due to high pressure")
            return True

        if fuel_pre_press_open and fuel_average > FUEL_TARGET - NOMINAL_THRESHOLD:
            ox_prepress.close()
            return True
        
    with client.control.acquire("Reg Fuel Fire", ACKS + PTS, CMDS, 200) as auto:
        try:
            time.sleep(1)
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

            syauto.close_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso, fuel_vent, ox_low_flow_vent, press_vent])
            time.sleep(2)

            print("repressurizing fuel and ox")
            auto.wait_until(fuel_pressurized)
            
            input("Press enter to continue")
        
            syauto.open_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso])
            print("start wait")
            time.sleep(FIRE_DURATION)
            print("end wait")
            syauto.open_close_many_valves(auto,[fuel_vent, ox_low_flow_vent, press_vent],[fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso])

        except KeyboardInterrupt:
            syauto.open_close_many_valves(auto,[fuel_vent, ox_low_flow_vent, press_vent],[fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso])
            print("Manual abort, safing system")

def reg_ox_fire():
    NOMINAL_THRESHOLD = 20
    FIRE_DURATION = 25
    def ox_pressurized(auto: Controller) -> bool:
        averages = get_averages(auto, PTS)
        ox_average = statistics.median([averages[OX_PT_1], averages[OX_PT_2], averages[OX_PT_3]])
        ox_pre_press_open = auto[OX_PRE_PRESS_ACK]

        if ox_pre_press_open and ox_average >= OX_TARGET:
            ox_prepress.close()

        if not ox_pre_press_open and ox_average < OX_TARGET - NOMINAL_THRESHOLD:
            ox_prepress.open()    


        if ox_pre_press_open and ox_average > MAX_OX_PRESSURE:
            ox_prepress.close()
            print("ABORTING OX due to high pressure")
            return True

        if ox_pre_press_open and ox_average > OX_TARGET - NOMINAL_THRESHOLD:
            ox_prepress.close()
            return True
        
    with client.control.acquire("Reg Ox Fire", ACKS + PTS, CMDS, 200) as auto:
        try:
            time.sleep(1)
            ox_prevalve = syauto.Valve(auto=auto, cmd=OX_PREVALVE_CMD, ack=OX_PREVALVE_ACK, normally_open=False)
            ox_press_iso = syauto.Valve(auto=auto, cmd = OX_PRESS_ISO_CMD, ack = OX_PRESS_ISO_ACK, normally_open=False)
            ox_dome_iso = syauto.Valve(auto=auto, cmd = OX_DOME_ISO_CMD, ack = OX_DOME_ISO_ACK, normally_open=False)
            ox_low_flow_vent = syauto.Valve(auto=auto, cmd = OX_LOW_FLOW_VENT_CMD, ack = OX_LOW_FLOW_VENT_ACK, normally_open=True)
            ox_prepress = syauto.Valve(auto=auto, cmd = OX_PRE_PRESS_CMD, ack = OX_PRE_PRESS_ACK, normally_open=False)

            syauto.close_all(auto, [ox_prevalve, ox_press_iso, ox_dome_iso, ox_low_flow_vent])
            time.sleep(2)

            print("repressurizing fuel and ox")
            auto.wait_until(ox_pressurized)
            
            input("Press enter to continue")
        
            syauto.open_all(auto, [ox_prevalve, ox_press_iso, ox_dome_iso])
            print("start wait")
            time.sleep(FIRE_DURATION)
            print("end wait")
            syauto.open_close_many_valves(auto,[ ox_low_flow_vent],[ox_prevalve, ox_press_iso, ox_dome_iso])

        except KeyboardInterrupt:
            syauto.open_close_many_valves(auto,[ox_low_flow_vent],[ox_prevalve, ox_press_iso, ox_dome_iso])
            print("Manual abort, safing system")


def pre_press():
    with client.control.acquire(name="Pre press coldflow autosequence", write=WRITE_TO, read=READ_FROM, write_authorities=200) as auto:
            ###     DECLARES THE VALVES WHICH WILL BE USED     ###
        fuel_pre_press = syauto.Valve(auto, FUEL_PRE_PRESS_CMD, FUEL_PRE_PRESS_ACK, normally_open=False)
        fuel_vent = syauto.Valve(auto, FUEL_VENT_CMD, FUEL_VENT_ACK, normally_open=True)
        ox_pre_press = syauto.Valve(auto, OX_PRE_PRESS_CMD, OX_PRE_PRESS_ACK, normally_open=False)
        ox_low_flow_vent = syauto.Valve(auto, OX_LOW_FLOW_VENT_CMD, OX_LOW_FLOW_VENT_ACK, normally_open=True)
        valves = [fuel_pre_press, ox_pre_press]
        vents = [fuel_vent, ox_low_flow_vent]

        def pre_press(auto_: Controller):
            averages = get_averages(auto_, PTS)
            fuel_average = statistics.median([averages[FUEL_PT_1], averages[FUEL_PT_2], averages[FUEL_PT_3]])
            ox_average = statistics.median([averages[OX_PT_1], averages[OX_PT_2], averages[OX_PT_3]])
            fuel_pre_press_open = auto_[FUEL_PRE_PRESS_ACK]
            if (fuel_average < LOWER_FUEL_PRESSURE and not fuel_pre_press_open):
                fuel_pre_press.open()

            if (fuel_average > UPPER_FUEL_PRESSURE and fuel_pre_press_open):
                fuel_pre_press.close()

            ox_pre_press_open = auto_[OX_PRE_PRESS_ACK]
            if (ox_average < LOWER_OX_PRESSURE and not ox_pre_press_open):
                ox_pre_press.open()

            if (ox_average > UPPER_OX_PRESSURE and ox_pre_press_open):
                ox_pre_press.close()

            if (fuel_average > MAX_FUEL_PRESSURE):
                fuel_abort(auto_)
                return

            if (ox_average > MAX_OX_PRESSURE):
                ox_abort(auto_)
                return


            # aborts
            def ox_abort(auto_: Controller):
                print("aborting ox tanks")
                syauto.close_all(auto_, [ox_pre_press])
                input("Would you like to open ox low flow vent? y/n")
                if (input == "y"):
                    syauto.open_all(auto_, [ox_low_flow_vent])
                    print("ox_low_flow_vent safed")
                input("Press any key to continue pressing or ctrl+c to abort")


            def fuel_abort(auto_: Controller):
                print("aborting fuel tanks")
                syauto.close_all(auto_, [fuel_pre_press])
                input("Would you like to open fuel vent? y/n")
                if (input == "y"):
                    syauto.open_all(auto, [fuel_vent])
                    print("fuel_vent safed")
                input("Press any key to continue pressing or ctrl+c to abort")


        ###     RUNS ACTUAL AUTOSEQUENCE         ###
            try:
                start = sy.TimeStamp.now()
                time.sleep(1)
                # starts by closing all valves and closing all vents
                print("Starting Pre Press Autosequence. Setting initial system state.")
                syauto.open_close_many_valves(auto, [], vents + valves)
                time.sleep(2)

                print(auto[FUEL_PRE_PRESS_ACK])

                print("starting pre press")
                auto.wait_until(pre_press)

                # print("Pre press complete. Safing System")
                # syauto.close_all(auto, [vents + valves])
                # print("Valves and vents are now closed. Autosequence complete.")

                # Creating a range inside autosequences
                rng = client.ranges.create(
                    name=f"{start.__str__()[11:16]} Pre Press Coldflow Sim",
                    time_range=sy.TimeRange(start, sy.TimeStamp.now()),
                )


            # ctrl+c interrupt
            # close all vents and valves
            # gives user opetion to open vents
            except KeyboardInterrupt:
                print("Test interrupted. Safeing System")
                syauto.close_all(auto, vents + valves)
                input("Do we want to open vents? y/n")
                if (input == "y"):
                    syauto.open_all(auto=auto, valves=vents)
                print("Autosequence ended")

            time.sleep(60)

if REG_FUEL_FIRE == True:
    reg_fuel_fire()

if REG_OX_FIRE == True:
    reg_ox_fire()

if PRE_PRESS == True:
    pre_press()

        

