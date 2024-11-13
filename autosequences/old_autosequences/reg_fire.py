import syauto
import time
from synnax.control.controller import Controller
import synnax as sy
import statistics
from collections import deque

# this connects to the synnax simulation server
# client = sy.Synnax(
#     host="localhost",
#     port=9090,
#     username="synnax",
#     password="seldon",
#     secure=False
# )

# Connects to masa cluster
client = sy.Synnax(
    host="synnax.masa.engin.umich.edu",
    port=80,
    username="synnax",
    password="seldon",
    secure=True
)

REG_FUEL_FIRE = True
REG_OX_FIRE = True

# change names and numbers to match the actual channels
# valve names to channel names
FUEL_VENT_ACK = "gse_doa_15"
FUEL_VENT_CMD = "gse_doc_15"
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
ACKS = [FUEL_PREVALVE_ACK, OX_PREVALVE_ACK, FUEL_PRESS_ISO_ACK, OX_PRESS_ISO_ACK, OX_DOME_ISO_ACK, FUEL_VENT_ACK, OX_LOW_FLOW_VENT_ACK, PRESS_VENT_ACK]
CMDS = [FUEL_PREVALVE_CMD, OX_PREVALVE_CMD, FUEL_PRESS_ISO_CMD, OX_PRESS_ISO_CMD, OX_DOME_ISO_CMD, FUEL_VENT_CMD, OX_LOW_FLOW_VENT_CMD, PRESS_VENT_CMD]

# List of channels we're going to read from and write to
WRITE_TO = []
READ_FROM = []
for cmd_chan in CMDS:
    WRITE_TO.append(cmd_chan)
for ack_chan in ACKS:
    READ_FROM.append(ack_chan)
for PT_chan in PTS:
    READ_FROM.append(PT_chan)
print(WRITE_TO)
print(READ_FROM)

# TODO: update these before running the autosequence

# TARGET_FUEL_PRESSURE = 500  # Fuel Reg Set Pressure
# UPPER_FUEL_PRESSURE = TARGET_FUEL_PRESSURE + 10
# LOWER_FUEL_PRESSURE = TARGET_FUEL_PRESSURE - 10
# UPPER_FINAL_FUEL_PRESSURE = 490  # FUEL TEST PRESSURE
# LOWER_FINAL_FUEL_PRESSURE = UPPER_FINAL_FUEL_PRESSURE - 20
MAX_FUEL_PRESSURE = 575

# TARGET_OX_PRESSURE = 490  # Ox Reg Set Pressure
# UPPER_OX_PRESSURE = TARGET_OX_PRESSURE + 10
# LOWER_OX_PRESSURE = TARGET_OX_PRESSURE - 10
# UPPER_FINAL_OX_PRESSURE = 450  # OX REG SET PRESSURE
# LOWER_FINAL_OX_PRESSURE = UPPER_FINAL_OX_PRESSURE - 20
MAX_OX_PRESSURE = 575

RUNNING_AVERAGE_LENGTH = 5  # samples
# at 50Hz data, this means 0.1s

FIRE_DURATION = 25

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


with client.control.acquire("Pre Press + Reg Fire", READ_FROM, WRITE_TO, 200) as auto:
    fuel_prevalve = syauto.Valve(auto=auto, cmd=FUEL_PREVALVE_CMD, ack=FUEL_PREVALVE_ACK, normally_open=False)
    ox_prevalve = syauto.Valve(auto=auto, cmd=OX_PREVALVE_CMD, ack=OX_PREVALVE_ACK, normally_open=False)
    fuel_press_iso = syauto.Valve(auto=auto, cmd = FUEL_PRESS_ISO_CMD, ack = FUEL_PRESS_ISO_ACK, normally_open=False)
    ox_press_iso = syauto.Valve(auto=auto, cmd = OX_PRESS_ISO_CMD, ack = OX_PRESS_ISO_ACK, normally_open=False)
    ox_dome_iso = syauto.Valve(auto=auto, cmd = OX_DOME_ISO_CMD, ack = OX_DOME_ISO_ACK, normally_open=False)
    fuel_vent = syauto.Valve(auto=auto, cmd = FUEL_VENT_CMD, ack = FUEL_VENT_ACK, normally_open=True)
    ox_low_flow_vent = syauto.Valve(auto=auto, cmd = OX_LOW_FLOW_VENT_CMD, ack = OX_LOW_FLOW_VENT_ACK, normally_open=True)
    press_vent = syauto.Valve(auto=auto, cmd = PRESS_VENT_CMD, ack = PRESS_VENT_ACK, normally_open=True)

    print("Setting starting state")
    syauto.close_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso, fuel_vent, ox_low_flow_vent, press_vent])
    time.sleep(2)    

    def reg_fire():
        # auto.wait_until(over_pressurize)

        print("commencing fire")
        syauto.open_all(auto, [ox_dome_iso, ox_press_iso])
        time.sleep(2)
        syauto.open_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso])
        time.sleep(FIRE_DURATION)
        syauto.open_close_many_valves(auto,[fuel_vent, ox_low_flow_vent, press_vent, ox_dome_iso],[fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso])
        print("terminating fire")


    # this block runs the overall sequence
    try:
            start = sy.TimeStamp.now()
            syauto.close_all(auto, [fuel_vent, ox_low_flow_vent, press_vent, ox_dome_iso, fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso])
            time.sleep(1)

            print("initiating regfire")
            reg_fire()
            # the above statement will only finish if an abort is triggered

    except KeyboardInterrupt as e:
        syauto.close_all(auto, [fuel_prevalve, ox_prevalve, fuel_press_iso, ox_press_iso, ox_dome_iso])

        ans = input("Aborting - would you like to open vents? y/n ")
        if ans == "y":
            syauto.open_all(auto, [fuel_vent, ox_low_flow_vent, press_vent])

        # this creates a range in synnax so we can view the data
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Pre Press Coldflow Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )
