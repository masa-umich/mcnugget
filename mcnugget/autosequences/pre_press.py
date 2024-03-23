"""
### OVERVIEW ###

This autosequence pressurizes the Ox and Fuel Tanks

1. Set Starting State
    - Energize all normally_open (close vents)
    - Energize ox and fuel prevalve and deenergize all other valves

2. Pressurize at a rate of 1000psi / 15 min 
    - Open ox and fuel pre-press 
    - Pressurize ox tanks until ~415 psi
    - Pressurize fuel tanks until ~460 psi
    *pressures can change based on testing requirements

3. Normal test end 
    - Close all valves

4. Abort
    - Close all valves
    - User input y/n
        - y: open vents
        - n: leave vents closed
---
### IMPORTANT INFO ###

When determining fuel and ox tank pressures
    - Take the average of each PT
    - Take the median of the averages

When determining TC readings
    - Take the average of each TC
    - Take the median of the averages

Any of these conditions will trigger an abort
    - 2/3 PTs reading an invalid value (below -100 or above MAWP)
    - 3/4 TCs reading an invalid temperature (above 140)

auto.wait_until(lambda function) is a function which returns when the defined lambda returns TRUE

We will use the runsafe_press_tank_fill(TARGET) function as our lambda, which will check
    - whether 2/3 PTs read invalid pressures (> MAX_PRESSURE, < -100) -> ABORT
    - whether 3/4 TCs read invalid temperatures (> MAX_TEMPERATURE) -> ABORT
    - whether the median PT is above the target temperature -> RETURN

This will allow us to safely pressurize in increments. The custom pressurize function will also
    require a manual confirm if any of the TCs read a temperature above 120 farenheight.

---
### VALVES LIST ###

For this test, the only valves we will need to control are:

    ---VALVES---
    Fuel Pre Press
    Ox Pre Press

    ---VENTS---
    Ox Low Flow Vent
    Fuel Vent

    ---PT CHANNELS---
    Ox Tank PT 1, 2, and 3
    Fuel Tank PT 1, 2, and 3

    ---TC CHANNELS---
    Ox Tank TC 1, 2, 3, and 4
    Fuel Tank TC 1, 2, 3, and 4
    *If TCS are ready

As such, all other valves/vents have been left out! Channel names are left in case they change the day of.

"""

import time
import synnax as sy
from synnax.control.controller import Controller
import syauto
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
FUEL_TANK_PT_1 = "gse_ai_3"
FUEL_TANK_PT_2 = "gse_ai_4"
FUEL_TANK_PT_3 = "gse_ai_35"
OX_TANK_PT_1 = "gse_ai_6"
OX_TANK_PT_2 = "gse_ai_7"
OX_TANK_PT_3 = "gse_ai_8"

PTS = [FUEL_TANK_PT_1, FUEL_TANK_PT_2, FUEL_TANK_PT_3, OX_TANK_PT_1, OX_TANK_PT_2, OX_TANK_PT_3]

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
#Pressures are in psi
FUEL_TANK_TARGET = 400
OX_TANK_TARGET = 400
UPPER_FUEL_TANK_PRESSURE = 420
LOWER_FUEL_TANK_PRESSURE = 380
MAX_FUEL_TANK_PRESSURE = 525
UPPER_OX_TANK_PRESSURE = 420
LOWER_OX_TANK_PRESSURE = 380
MAX_OX_TANK_PRESSURE = 525
# TODO: target + bound instead of upper/lower

RUNNING_AVERAGE_LENGTH = 20


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
    FUEL_TANK_PT_1: FUEL_PT_1_DEQUE,
    FUEL_TANK_PT_2: FUEL_PT_2_DEQUE,
    FUEL_TANK_PT_3: FUEL_PT_3_DEQUE,
    OX_TANK_PT_1: OX_PT_1_DEQUE,
    OX_TANK_PT_2: OX_PT_2_DEQUE,
    OX_TANK_PT_3: OX_PT_3_DEQUE
}

SUM_DICT = {
    FUEL_TANK_PT_1: FUEL_PT_1_SUM,
    FUEL_TANK_PT_2: FUEL_PT_2_SUM,
    FUEL_TANK_PT_3: FUEL_PT_3_SUM,
    OX_TANK_PT_1: OX_PT_1_SUM,
    OX_TANK_PT_2: OX_PT_2_SUM,
    OX_TANK_PT_3: OX_PT_3_SUM
}

with client.control.acquire(name="Pre press coldflow autosequence", write=WRITE_TO, read=READ_FROM, write_authorities=200) as auto:

    ###     DECLARES THE VALVES WHICH WILL BE USED     ###

    fuel_pre_press = syauto.Valve(auto, FUEL_PRE_PRESS_CMD, FUEL_PRE_PRESS_ACK,normally_open=False)
    fuel_vent = syauto.Valve(auto, FUEL_VENT_CMD, FUEL_VENT_ACK,normally_open=True)
    ox_pre_press = syauto.Valve(auto, OX_PRE_PRESS_CMD, OX_PRE_PRESS_ACK,normally_open=False)
    ox_low_flow_vent = syauto.Valve(auto, OX_LOW_FLOW_VENT_CMD, OX_LOW_FLOW_VENT_ACK,normally_open=True)
    valves = [fuel_pre_press, ox_pre_press]
    vents = [fuel_vent, ox_low_flow_vent]

    ###     DEFINES FUNCTIONS USED IN AUTOSEQUENCE         ###

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

    '''
    This function continously checks if an abort condition is hit
    If an abort condition is hit, it will close all valves and give the user the option to open the vents
    '''
    def pre_press (auto_:Controller):
        averages = get_averages(auto_, PTS)
        fuel_average = statistics.median([averages[FUEL_TANK_PT_1], averages[FUEL_TANK_PT_2], averages[FUEL_TANK_PT_3]])
        ox_average = statistics.median([averages[OX_TANK_PT_1], averages[OX_TANK_PT_2], averages[OX_TANK_PT_3]])
        if(fuel_average < LOWER_FUEL_TANK_PRESSURE):
            fuel_pre_press.open()
        
        if(fuel_average > UPPER_FUEL_TANK_PRESSURE):
            fuel_pre_press.close()
        
        if(ox_average < LOWER_OX_TANK_PRESSURE):
            ox_pre_press.open()

        if(ox_average > UPPER_OX_TANK_PRESSURE):
            ox_pre_press.close()
        
        if(fuel_average>MAX_FUEL_TANK_PRESSURE):
            fuel_abort(auto_)
            return

        if(ox_average>MAX_OX_TANK_PRESSURE):
            ox_abort(auto_)
            return

    #aborts 
    def ox_abort(auto_:Controller):
        print("aborting ox tanks")
        syauto.close_all(auto_, [ox_pre_press])
        input("Would you like to open ox low flow vent? y/n")
        if(input == "y"):
            syauto.open_all(auto_, [ox_low_flow_vent])
            print("ox_low_flow_vent safed")
        input("Press any key to continue pressing or ctrl+c to abort")

    def fuel_abort(auto_:Controller):
        print("aborting fuel tanks")
        syauto.close_all(auto_, [fuel_pre_press])
        input("Would you like to open fuel vent? y/n")
        if(input == "y"):
            syauto.open_all(auto, [fuel_vent])
            print("fuel_vent safed")
        input("Press any key to continue pressing or ctrl+c to abort")
            
    ###     RUNS ACTUAL AUTOSEQUENCE         ###
    try:
        start= sy.TimeStamp.now()
        # starts by closing all valves and closing all vents
        print("Starting Pre Press Autosequence. Setting initial system state.")
        syauto.open_close_many_valves(auto,[], vents + valves)
        time.sleep(1)

        print("starting pre press")
        auto.wait_until(pre_press)

        # print("Pre press complete. Safing System")
        # syauto.close_all(auto, [vents + valves])
        # print("Valves and vents are now closed. Autosequence complete.")

        #Creating a range inside autosequences
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Pre Press Coldflow Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

    
    #ctrl+c interrupt
    #close all vents and valves
    #gives user opetion to open vents
    except KeyboardInterrupt: 
        print("Test interrupted. Safeing System")
        syauto.close_all(auto, vents + valves)
        input("Do we want to open vents? y/n")
        if(input == "y"):
            syauto.open_all(auto=auto, valves=vents)
        print("Autosequence ended")

    time.sleep(60)
