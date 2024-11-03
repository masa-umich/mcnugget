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
from datetime import datetime, timedelta
import sys
import threading
import logging

#Prompts for user input as to whether we want to run a simulation or run an actual test
#If prompted to run a coldflow test, we will connect to the MASA remote server and have a delay of 60 seconds
real_test = False
mode = input("Enter 'real' for coldflow/hotfire or 'sim' to run a simulation: ")
if(mode == "real" or mode == "Real" or mode == "REAL"):
    real_test = True
    print("Testing mode")
    # this connects to the synnax testing server
    client = sy.Synnax(
    host="synnax.masa.engin.umich.edu",
    port=80,
    username="synnax",
    password="seldon",
    secure=True
    )

#If prompted to run a simulation, the delay will be 1 second and we will connect to the synnax simulation server
elif mode == "sim" or mode == "Sim" or mode == "SIM" or mode == "":
    real_test = False
    print("Simulation mode")
    # this connects to the synnax simulation server
    client = sy.Synnax(
        host="localhost",
        port=9090,
        username="synnax",
        password="seldon",
        secure=False
    )

else:
    print("Bestie what are you trying to do? If it's a typo, just try again, we're gonna close to program for now though <3")
    exit()


#Using FUEL or OX depending on user's command line input
boolFuel = False
boolOx = False 
if (len(sys.argv) == 1):
    boolFuel = True
    boolOx = True
elif (len(sys.argv) == 2):
    if (sys.argv[1] == "NOOX" or sys.argv[1] == "noox"):
        boolFuel = True
    elif (sys.argv[1] == "NOFUEL" or sys.argv[1] == "nofuel"):
        boolOx = True
    else:
        print("Specify with 'noox' or 'nofuel' or no arguments, closing program")
        exit()
else: 
    print("Bestie you want fuel and oxygen on or off? Closing program")
    exit()
#Tell user what the settings are
if (boolFuel and not boolOx):
    print("Running program with fuel on and oxygen off")
elif (not boolFuel and boolOx):
    print("Running program with fuel off and oxygen on")
else:
    print("Running program with fuel and oxygen on")

USING_FUEL = boolFuel

USING_OX = boolOx

# PRE_PRESS = False

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
FUEL_FEEDLINE_PURGE_CMD = "gse_doc_7"
FUEL_FEEDLINE_PURGE_ACK = "gse_doa_7"
OX_FEEDLINE_PURGE_CMD = "gse_doc_8"
OX_FEEDLINE_PURGE_ACK = "gse_doa_8"
# TODO: Update these based on instrumentation sheet
OX_MPV_CMD = "gse_doc_6"
OX_MPV_ACK = "gse_doa_6"
FUEL_MPV = "gse_doc_24"
FUEL_MPV_ACK = "gse_doa_24"
IGNITER_CMD = "gse_doc_25"
IGNITER_ACK = "gse_doa_25"

# Defining PT aliases
FUEL_PT_1 = "gse_ai_3"
FUEL_PT_2 = "gse_ai_4"
FUEL_PT_3 = "gse_ai_35"
OX_PT_1 = "gse_ai_6"
OX_PT_2 = "gse_ai_7"
OX_PT_3 = "gse_ai_8"

PTS = [FUEL_PT_1, FUEL_PT_2, FUEL_PT_3, OX_PT_1, OX_PT_2, OX_PT_3]
ACKS = [FUEL_PREVALVE_ACK, OX_PREVALVE_ACK, FUEL_PRESS_ISO_ACK, OX_PRESS_ISO_ACK, OX_DOME_ISO_ACK, 
        FUEL_VENT_ACK, OX_LOW_FLOW_VENT_ACK, PRESS_VENT_ACK, FUEL_PRE_PRESS_ACK, OX_PRE_PRESS_ACK,
        FUEL_FEEDLINE_PURGE_ACK, OX_FEEDLINE_PURGE_ACK,OX_MPV_ACK, FUEL_MPV_ACK, IGNITER_ACK]
CMDS = [FUEL_PREVALVE_CMD, OX_PREVALVE_CMD, FUEL_PRESS_ISO_CMD, OX_PRESS_ISO_CMD, OX_DOME_ISO_CMD, 
        FUEL_VENT_CMD, OX_LOW_FLOW_VENT_CMD, PRESS_VENT_CMD, FUEL_PRE_PRESS_CMD, OX_PRE_PRESS_CMD,
        FUEL_FEEDLINE_PURGE_CMD, OX_FEEDLINE_PURGE_CMD, OX_MPV_CMD, FUEL_MPV, IGNITER_CMD]

# List of channels we're going to read from and write to
WRITE_TO = []
READ_FROM = []
for cmd_chan in CMDS:
    WRITE_TO.append(cmd_chan)
for ack_chan in ACKS:
    READ_FROM.append(ack_chan)
for PT_chan in PTS:
    READ_FROM.append(PT_chan)
# print(WRITE_TO)
# print(READ_FROM)

# TODO: update these before running the autosequence

TARGET_FUEL_PRESSURE = 450  # Fuel Reg Set Pressure
UPPER_FUEL_PRESSURE = TARGET_FUEL_PRESSURE + 10
LOWER_FUEL_PRESSURE = TARGET_FUEL_PRESSURE - 10
MAX_FUEL_PRESSURE = 575

TARGET_OX_PRESSURE = 460  # Ox Reg Set Pressure
UPPER_OX_PRESSURE = TARGET_OX_PRESSURE + 10
LOWER_OX_PRESSURE = TARGET_OX_PRESSURE - 10
MAX_OX_PRESSURE = 575

RUNNING_AVERAGE_LENGTH = 5  # samples
# at 50Hz data, this means 0.1s

FIRE_DURATION = 20

# MPV_DELAY is set such that OX is put in the chamber 0.200 seconds before fuel
ox_time_to_reach_chamber = 0.357
fuel_time_to_reach_chamber = 0.276
MPV_DELAY = 0.2 + ox_time_to_reach_chamber - fuel_time_to_reach_chamber   # seconds
# OX_MPV takes 0.357 s to reach chamber
# FUEL_MPV used to take 0.246 s to reach chamber
# FUEL_MPV now takes 0.276 s to reach chamber
# This delay puts OX in the chamber 0.200 seconds before fuel

# IGNITER_DELAY = 6  # seconds
ISO_DELAY = 2  # seconds


# Running average implementation
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

# state variable tells which part of the autosequence we are in 
#       settings are [before prepress, after prepress before ignition, after ignition] 
PROGRAM_STATE = ""
with client.control.acquire("Pre Press + Reg Fire", READ_FROM, WRITE_TO, 200) as auto:
    # creates valve objects for each valve
    fuel_prepress = syauto.Valve(auto=auto, cmd = FUEL_PRE_PRESS_CMD, ack = FUEL_PRE_PRESS_ACK, normally_open=False)
    ox_prepress = syauto.Valve(auto=auto, cmd = OX_PRE_PRESS_CMD, ack = OX_PRE_PRESS_ACK, normally_open=False)
    fuel_feedline_purge = syauto.Valve(auto=auto, cmd = FUEL_FEEDLINE_PURGE_CMD, ack = FUEL_FEEDLINE_PURGE_ACK, normally_open=False)
    ox_feedline_purge = syauto.Valve(auto=auto, cmd = OX_FEEDLINE_PURGE_CMD, ack = OX_FEEDLINE_PURGE_ACK, normally_open=False)
    fuel_press_iso = syauto.Valve(auto=auto, cmd = FUEL_PRESS_ISO_CMD, ack = FUEL_PRESS_ISO_ACK, normally_open=False)
    ox_press_iso = syauto.Valve(auto=auto, cmd = OX_PRESS_ISO_CMD, ack = OX_PRESS_ISO_ACK, normally_open=False)
    ox_dome_iso = syauto.Valve(auto=auto, cmd = OX_DOME_ISO_CMD, ack = OX_DOME_ISO_ACK, normally_open=False)
    fuel_prevalve = syauto.Valve(auto=auto, cmd=FUEL_PREVALVE_CMD, ack=FUEL_PREVALVE_ACK, normally_open=False)
    ox_prevalve = syauto.Valve(auto=auto, cmd=OX_PREVALVE_CMD, ack=OX_PREVALVE_ACK, normally_open=False)
    fuel_vent = syauto.Valve(auto=auto, cmd = FUEL_VENT_CMD, ack = FUEL_VENT_ACK, normally_open=True)
    ox_low_flow_vent = syauto.Valve(auto=auto, cmd = OX_LOW_FLOW_VENT_CMD, ack = OX_LOW_FLOW_VENT_ACK, normally_open=True)
    press_vent = syauto.Valve(auto=auto, cmd = PRESS_VENT_CMD, ack = PRESS_VENT_ACK, normally_open=True)
    fuel_mpv = syauto.Valve(auto=auto, cmd = FUEL_MPV, ack = FUEL_MPV_ACK, normally_open=True)
    ox_mpv = syauto.Valve(auto=auto, cmd = OX_MPV_CMD, ack = OX_MPV_ACK, normally_open=True)
    igniter = syauto.Valve(auto=auto, cmd = IGNITER_CMD, ack = IGNITER_ACK, normally_open=False)

    # # For determining if each valve is open 
    # fuel_prevalve_open = auto[FUEL_PREVALVE_ACK]
    # ox_prevalve_open = auto[OX_PREVALVE_ACK]
    # fuel_press_iso_open = auto[FUEL_PRESS_ISO_ACK]
    # ox_press_iso_open = auto[OX_PRESS_ISO_ACK]
    # ox_dome_iso_open = auto[OX_DOME_ISO_ACK]
    # fuel_vent_open = auto[FUEL_VENT_ACK]
    # ox_low_flow_vent_open = auto[OX_LOW_FLOW_VENT_ACK]
    # fuel_prepress_open = auto[FUEL_PRE_PRESS_ACK]
    # ox_prepress_open = auto[OX_PRE_PRESS_ACK]
    # press_vent_open = auto[PRESS_VENT_ACK]
    # fuel_mpv_open = auto[FUEL_MPV_ACK]
    # ox_mpv_open = auto[OX_MPV_ACK]
    # igniter_open = auto[IGNITER_ACK]

    user_input_received = threading.Event()


    def fuel_ox_abort(auto: Controller, abort_fuel=False, abort_ox=False):
        valves_to_close = []
        valves_to_potentially_open = []
        if abort_fuel:
            print("ABORTING FUEL")
            valves_to_close += [fuel_prepress]
            valves_to_potentially_open += [fuel_vent]
        if abort_ox:
            print("ABORTING OX")
            valves_to_close += [ox_prepress]
            valves_to_potentially_open += [ox_low_flow_vent]
        syauto.close_all(auto, valves_to_close)
        ans = input("would you like to open vents? y/n ")
        if ans == "y" or ans == "Y" or ans == "yes":
            syauto.open_all(auto, valves_to_potentially_open)
            if (PROGRAM_STATE == "after prepress before ignition"):
                syauto.close_all([fuel_prevalve, ox_prevalve])
        #input("Press any key to continue or ctrl-c to fully abort")
        
    def pressurize(auto: Controller) -> bool:
    
        averages = get_averages(auto, PTS)
        ox_average = statistics.median([averages[OX_PT_1], averages[OX_PT_2], averages[OX_PT_3]])
        ox_pre_press_open = auto[OX_PRE_PRESS_ACK]
        fuel_average = statistics.median([averages[FUEL_PT_1], averages[FUEL_PT_2], averages[FUEL_PT_3]])
        fuel_pre_press_open = auto[FUEL_PRE_PRESS_ACK]

        if USING_FUEL:
            if fuel_pre_press_open and (fuel_average >= UPPER_FUEL_PRESSURE):
                print("fuel repressurized")
                fuel_prepress.close()

            if (not fuel_pre_press_open) and (fuel_average < LOWER_FUEL_PRESSURE):
                print("repressurizing fuel")
                fuel_prepress.open()

            if fuel_pre_press_open and (fuel_average > MAX_FUEL_PRESSURE):
                fuel_prepress.close()
                print("ABORTING FUEL due to high pressure")
                if USING_OX:
                    if ox_pre_press_open and (ox_average > MAX_OX_PRESSURE):
                        print("ABORTING OX due to high pressure")
                        fuel_ox_abort(auto, abort_fuel=True, abort_ox=True)

                fuel_ox_abort(auto, abort_fuel=True, abort_ox=False)

        if USING_OX:
            if ox_pre_press_open and (ox_average >= UPPER_OX_PRESSURE):
                print("ox repressurized")
                ox_prepress.close()

            if (not ox_pre_press_open) and (ox_average < LOWER_OX_PRESSURE):
                print("repressurizing ox")
                ox_prepress.open()    

            if ox_pre_press_open and ox_average > MAX_OX_PRESSURE:
                print("ABORTING OX due to high pressure")
                fuel_ox_abort(auto, abort_fuel=False, abort_ox=True)

    def get_user_input():
        # Function to get user input for firing sequence.
        # Sets the event once input is received.
        global user_input_received
        answer = input("\nValves are closed. Input `fire` to commence firing sequence. Press enter to abort autosequence.\n")
        
        # Signal that user input has been received
        user_input_received.set()
        
        if answer == 'fire':
            print("Firing sequence commenced!")
            reg_fire()
        elif answer == '':
            fuel_ox_abort(auto, USING_FUEL, USING_OX)

        #elif answer == 'vent':
            #ans = input("Confirm hard abort - would you like to open vents and close prevalves? y/n ")
            #if ans == "y":
                #syauto.open_close_many_valves(auto, [fuel_vent, ox_low_flow_vent, press_vent], [fuel_prevalve, ox_prevalve])

    def wait_until_pressurized(auto: Controller, condition) -> None:
        #keeps pressurizing until user inputs
        while not user_input_received.is_set():
            condition(auto)
            time.sleep(0.1)  
 
    def reg_fire():
        fuel_prepress.close()
        ox_prepress.close()
        opened_fuel_mpv = False
        opened_ox_mpv = False
        PROGRAM_STATE = "after ignition"
        try: 
            print("commencing fire sequence - firing in: ")
            time.sleep(1)
            print("10")
            time.sleep(1)
            print("9")
            time.sleep(1)
            print("8")
            time.sleep(1)
            print("7")
            time.sleep(1)

            print("6 energizing the igniter")
            igniter.open()
            time.sleep(1)
            print("5 deenergizing the igniter")
            igniter.close()
            time.sleep(1)
            print("4")
            time.sleep(1)
            
            print("3")
            time.sleep(1)

            if (USING_FUEL and not USING_OX):
                print("2")
                time.sleep(1)
                print("1")
                time.sleep(1)

                print("0 Opening Fuel ISO")
                syauto.open_all(auto, [fuel_press_iso])

                time.sleep(MPV_DELAY)
                print("Opening Fuel MPV")
                syauto.open_all(auto, [fuel_mpv])
                opened_fuel_mpv = True

            elif (not USING_FUEL and USING_OX):
                print("2 Opening Ox Dome Iso and Ox Press Iso")
                syauto.open_all(auto, [ox_dome_iso, ox_press_iso])
                time.sleep(1)
                print("1")
                time.sleep(1)

                print("0 Opening Ox MPV")
                syauto.open_all(auto, [ox_mpv])
                opened_ox_mpv = True

            else:
                print("2 Opening Ox Dome Iso and Ox Press Iso")
                syauto.open_all(auto, [ox_dome_iso, ox_press_iso])
                time.sleep(1)
                print("1")
                time.sleep(1)
                
                print("0 Opening Fuel ISO and Ox MPV")
                syauto.open_all(auto, [fuel_press_iso, ox_mpv])
                opened_ox_mpv = True

                # print(f"Opening Fuel MPV in {MPV_DELAY}")
                time.sleep(MPV_DELAY)
                print("Opening Fuel MPV")
                syauto.open_all(auto, [fuel_mpv])
                opened_fuel_mpv = True

            print(f"\nTerminating fire in")
            for i in range(FIRE_DURATION):
                print(f"{FIRE_DURATION - i}")
                time.sleep(1)

            print("Terminating fire")
            print("Opening vents and closing ISOs")
            syauto.open_close_many_valves(auto, [fuel_vent, ox_low_flow_vent, press_vent],[fuel_press_iso, ox_press_iso])
            if opened_fuel_mpv:
                print("Opening fuel feedline purge")
                fuel_feedline_purge.open()
            if opened_ox_mpv:
                print("Opening ox feedline purge")
                ox_feedline_purge.open()
            # time.sleep(0.5)
            if opened_fuel_mpv:
                print("Closing fuel prevalve")
                fuel_prevalve.close()
            if opened_ox_mpv:
                print("Closing ox prevalve")
                ox_prevalve.close()
            time.sleep(5)
            print("Closing dome ISO")
            syauto.close_all(auto, [ox_dome_iso])
            print("\nFiring sequence has been completed nominally")
        except KeyboardInterrupt:
            print("\nFiring sequence aborted, closing all valves and opening all vents")
            syauto.open_close_many_valves(auto,[fuel_vent, ox_low_flow_vent, press_vent, ox_dome_iso],[fuel_press_iso, ox_press_iso])
            time.sleep(0.5)
            if opened_fuel_mpv:
                print("Opening fuel feedline purge and closing fuel prevalve")
                syauto.open_close_many_valves(auto, [fuel_feedline_purge], [fuel_prevalve])
            if opened_ox_mpv:
                print("Opening ox feedline purge and closing ox prevalve")
                syauto.open_close_many_valves(auto, [ox_feedline_purge], [ox_prevalve])
            time.sleep(5)
            print("Closing dome ISO")
            syauto.close_all(auto, [ox_dome_iso])
            print("Terminating abort")
        time.sleep(10)
        # # this creates a range in synnax so we can view the data
        # if real_test:
        #     rng = client.ranges.create(
        #         name=f"{start.__str__()[11:16]} Pre Press + Hotfire",
        #         time_range=sy.TimeRange(start, datetime.now() + timedelta.min(2)),
        #     )
        #     print(f"Created range for test: {rng.name}")
        exit()

    # this block runs the overall sequence

    try:
        start = datetime.now()

        PROGRAM_STATE = "before prepress"
        time.sleep(1)
    
        #Check prevalves are opened or closed
        if (USING_FUEL and not USING_OX):
            if (auto[FUEL_PREVALVE_ACK]):
                input("Fuel prevalve open, press enter to continue ")
            else:
                ans = input("Fuel prevalve NOT open, type 'bypass' to continue ")
                if (ans != 'bypass'):
                    print('closing program')
                    exit()
        elif (not USING_FUEL and USING_OX):
            if (auto[OX_PREVALVE_ACK]):
                input("Ox prevalve open, press enter to continue ")
            else:
                ans = input("Fuel prevalve NOT open, type 'bypass' to continue ")
                if (ans != 'bypass'):
                    print('closing program')
                    exit()
        else:
            if (auto[FUEL_PREVALVE_ACK] and auto[OX_PREVALVE_ACK]):
                input("Prevalves open, press enter to continue ")
            else:
                ans = input("Fuel and/or Ox prevalve NOT open, type 'bypass' to continue ")
                if (ans != 'bypass'):
                    print('closing program')
                    exit()

        ans = input("Type 'start' to commence autosequence. ")
        if not (ans == 'start' or ans == 'Start' or ans == 'START'):
            exit()

        print("Setting starting state")
        syauto.close_all(auto, [ox_press_iso, ox_dome_iso, fuel_vent, ox_low_flow_vent, press_vent, ox_prepress, fuel_prepress, fuel_press_iso])

        
        if (USING_FUEL and not USING_OX):
            print("Pressurizing fuel in 6 seconds")
        elif (not USING_FUEL and USING_OX):
            print("Pressurizing ox in 6 seconds")
        else:
            print("Pressurizing fuel and ox in 6 seconds")

        time.sleep(1)
        for i in range(5):
            print(f"{5 - i}")
            time.sleep(1)


        if (USING_FUEL and not USING_OX):
            print("Pressurizing fuel")
        elif (not USING_FUEL and USING_OX):
            print("Pressurizing ox")
        else:
            print("Pressurizing fuel and ox")

        PROGRAM_STATE = "after prepress before ignition"
        auto.wait_until(pressurize)

    except KeyboardInterrupt as e:

        if (PROGRAM_STATE == "before prepress"):
            fuel_ox_abort(auto, USING_FUEL, USING_OX)

        elif (PROGRAM_STATE == "after prepress before ignition"):
            wait_thread = threading.Thread(target=wait_until_pressurized, args=(auto, pressurize))
            input_thread = threading.Thread(target=get_user_input)

            wait_thread.start()
            input_thread.start()

            wait_thread.join()
            input_thread.join()  
