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
    Fuel Pre Valve
    Ox Pre Valve
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
FUEL_PRE_PRESS_ACK = "gse_doa_11"
FUEL_PRE_PRESS_CMD = "gse_doc_11"
FUEL_VENT_ACK = "gse_doa_15"
FUEL_VENT_CMD = "gse_doc_15"
OX_PRE_PRESS_ACK = "gse_doa_12"
OX_PRE_PRESS_CMD = "gse_doc_12"
OX_LOW_FLOW_VENT_ACK = "gse_doa_16"
OX_LOW_FLOW_VENT_CMD = "gse_doc_16"
FUEL_TANK_PT_1 = "gse_ai_3"
FUEL_TANK_PT_2 = "gse_ai_4"
FUEL_TANK_PT_3 = "gse_ai_35"
OX_TANK_PT_1 = "gse_ai_1"
OX_TANK_PT_2 = "gse_ai_2"
OX_TANK_PT_3 = "gse_ai_34"

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


# TODO:
# PLEASE UPDATE/CONFIRM ALL VARIABLES BEFORE RUNNING TEST
FUEL_TANK_TARGET = 400
OX_TANK_TARGET = 400
MAX_FUEL_TANK_PRESSURE = 500
MAX_OX_TANK_PRESSURE = 500

with client.control.acquire(name="Pre press coldflow autosequence", write=WRITE_TO, read=READ_FROM, write_authorities=200) as auto:

    ###     DECLARES THE VALVES WHICH WILL BE USED     ###

    fuel_pre_press = syauto.Valve(auto, FUEL_PRE_PRESS_CMD, FUEL_PRE_PRESS_ACK)
    fuel_vent = syauto.Valve(auto, FUEL_VENT_CMD, FUEL_VENT_ACK)
    ox_pre_press = syauto.Valve(auto, OX_PRE_PRESS_CMD, OX_PRE_PRESS_ACK)
    ox_low_flow_vent = syauto.Valve(auto, OX_LOW_FLOW_VENT_CMD, OX_LOW_FLOW_VENT_ACK)
    valves = [fuel_pre_press, ox_pre_press]
    vents = [fuel_vent, ox_low_flow_vent]

    ###     DEFINES FUNCTIONS USED IN AUTOSEQUENCE         ###

    def compute_medians(channels: list[str]):
        # this function takes in a list of channel names and returns a list
            # where each channel name is replaced by its reading, averaged over RUNNING_MEDIAN_SIZE readings
        output = []
        for channel in channels:
            output.append(statistics.mean(auto[channel]))

        return output
    '''
    This function continously checks if an abort condition is hit
    If an abort condition is hit, it will close all valves and give the user the option to open the vents
    '''
    def pre_press_abort_check ():
        fuel_tank_pressure = compute_medians([FUEL_TANK_PT_1, FUEL_TANK_PT_2, FUEL_TANK_PT_3])
        ox_tank_pressure = compute_medians([OX_TANK_PT_1, OX_TANK_PT_2, OX_TANK_PT_3])
        if (fuel_tank_pressure > MAX_FUEL_TANK_PRESSURE):
            print("Fuel tank pressure is too high. Aborting.")
            fuel_abort()
        
        if (ox_tank_pressure > MAX_OX_TANK_PRESSURE):
            print("Ox tank pressure is too high. Aborting.")
            ox_abort()

    #aborts 
    def ox_abort():
        print("aborting ox tanks")
        syauto.close_all(auto, [ox_pre_press])
        input("Would you like to open ox low flow vent? y/n")
        if(input == "y"):
            syauto.open_all(auto, [ox_low_flow_vent])
            print("ox_low_flow_vent safed")

    def fuel_abort():
        print("aborting fuel tanks")
        syauto.close_all(auto, [fuel_pre_press])
        input("Would you like to open fuel vent? y/n")
        if(input == "y"):
            syauto.open_all(auto, [fuel_vent])
            print("fuel_vent safed")
            
    ###     RUNS ACTUAL AUTOSEQUENCE         ###
    try:
        start= sy.TimeStamp.now()
        # starts by closing all valves and closing all vents
        print("Starting Pre Press Autosequence. Setting initial system state.")
        syauto.close_all(auto, vents + valves)
        time.sleep(1)

        print("starting pre press")
        syauto.open_all(auto, [fuel_pre_press, ox_pre_press])
        auto.wait_until(pre_press_abort_check)

        print("Pre press complete. Safing System")
        syauto.close_all(auto, [vents + valves])
        print("Valves and vents are now closed. Autosequence complete.")

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
