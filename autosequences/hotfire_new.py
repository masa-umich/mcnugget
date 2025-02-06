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


## PRESSURE TRANSDUCERS ###
PNEUMATICS_BOTTLE = "gse_pt_1"
TRAILER_PNEUMATICS = "gse_pt_2"
ENGINE_PNEUMATICS = "gse_pt_3"
PRESS_BOTTLE = "gse_pt_4"
OX_DOME_INLET = "gse_pt_5"
OX_POST_PILOT_REG = "gse_pt_6"
OX_DOME_REG = "gse_pt_7"
OX_POST_DOME = "gse_pt_8"
OX_FLOWMETER_INLET = "gse_pt_9"
OX_FLOWMETER_THROAT = "gse_pt_10"
MARGIN_1 = "gse_pt_11"
FUEL_FLOWMETER_INLET = "gse_pt_12"
FUEL_FLOWMETER_THROAT = "gse_pt_13"
MARGIN_2 = "gse_pt_14"
FUEL_DOME_INLET = "gse_pt_15"
FUEL_POST_PILOT_REG = "gse_pt_16"
FUEL_DOME_REG = "gse_pt_17"
FUEL_POST_DOME = "gse_pt_18"
FUEL_TANK_1 = "gse_pt_19"
FUEL_TANK_2 = "gse_pt_20"
FUEL_TANK_3 = "gse_pt_21"
CHAMBER_1 = "gse_pt_22"
CHAMBER_2 = "gse_pt_23"
REGEN_MANIFOLD = "gse_pt_24"
FUEL_MANIFOLD_1 = "gse_pt_25"
TORCH_2K_BOTTLE = "gse_pt_26"
TORCH_2K_BOTTLE_POST_REG = "gse_pt_27"
TORCH_NITROUS_BOTTLE = "gse_pt_28"
TORCH_NITROUS_BOTTLE_POST_REG = "gse_pt_29"
TORCH_ETHANOL_TANK = "gse_pt_30"
TORCH_BODY_1 = "gse_pt_31"
TORCH_BODY_2 = "gse_pt_32"
TORCH_BODY_3 = "gse_pt_33"
PURGE_2K_BOTTLE = "gse_pt_34"
PURGE_POST_REG = "gse_pt_35"
TRICKLE_PURGE_BOTTLE = "gse_pt_36"
TRICKLE_PURGE_POST_REG = "gse_pt_37"
OX_FILL = "gse_pt_38"
OX_TANK_1 = "gse_pt_39"
OX_TANK_2 = "gse_pt_40"
OX_TANK_3 = "gse_pt_41"
OX_LEVEL_SENSOR = "gse_pt_42"
PTS = [
    PNEUMATICS_BOTTLE,
    TRAILER_PNEUMATICS,
    ENGINE_PNEUMATICS,
    PRESS_BOTTLE,
    OX_DOME_INLET,
    OX_POST_PILOT_REG,
    OX_DOME_REG,
    OX_POST_DOME,
    OX_FLOWMETER_INLET,
    OX_FLOWMETER_THROAT,
    MARGIN_1,
    FUEL_FLOWMETER_INLET,
    FUEL_FLOWMETER_THROAT,
    MARGIN_2,
    FUEL_DOME_INLET,
    FUEL_POST_PILOT_REG,
    FUEL_DOME_REG,
    FUEL_POST_DOME,
    FUEL_TANK_1,
    FUEL_TANK_2,
    FUEL_TANK_3,
    CHAMBER_1,
    CHAMBER_2,
    REGEN_MANIFOLD,
    FUEL_MANIFOLD_1,
    TORCH_2K_BOTTLE,
    TORCH_2K_BOTTLE_POST_REG,
    TORCH_NITROUS_BOTTLE,
    TORCH_NITROUS_BOTTLE_POST_REG,
    TORCH_ETHANOL_TANK,
    TORCH_BODY_1,
    TORCH_BODY_2,
    TORCH_BODY_3,
    PURGE_2K_BOTTLE,
    PURGE_POST_REG,
    TRICKLE_PURGE_BOTTLE,
    TRICKLE_PURGE_POST_REG,
    OX_FILL,
    OX_TANK_1,
    OX_TANK_2,
    OX_TANK_3,
    OX_LEVEL_SENSOR,
]

### VALVES ###
OX_RETURN_LINE = "gse_vlv_1"
OX_RETURN_LINE_STATE = "gse_state_1"
OX_FILL = "gse_vlv_2"
OX_FILL_STATE = "gse_state_2"
OX_PREVALVE = "gse_vlv_3"
OX_PREVALVE_STATE = "gse_state_3"
OX_DRAIN = "gse_vlv_4"
OX_DRAIN_STATE = "gse_state_4"
#OX_FEEDLINE_PURGE = "gse_vlv_5"
#OX_FEEDLINE_PURGE_STATE = "gse_state_5"
OX_FILL_PURGE = "gse_vlv_6"
OX_FILL_PURGE_STATE = "gse_state_6"
OX_PRE_PRESS = "gse_vlv_7"
OX_PRE_PRESS_STATE = "gse_state_7"
MPV_PURGE = "gse_vlv_8"
MPV_PURGE_STATE = "gse_state_8"
FUEL_PREPRESS = "gse_vlv_9"
FUEL_PREPRESS_STATE = "gse_state_9"
FUEL_PREVALVE = "gse_vlv_10"
FUEL_PREVALVE_STATE = "gse_state_10"
OX_MPV = "gse_vlv_11"
OX_MPV_STATE = "gse_state_11"
FUEL_MPV = "gse_vlv_12"
FUEL_MPV_STATE = "gse_state_12"
TORCH_FEEDLINE_PURGE = "gse_vlv_13"
TORCH_FEEDLINE_PURGE_STATE = "gse_state_13"
TORCH_ETHANOL_PRESS_ISO = "gse_vlv_14"
TORCH_ETHANOL_PRESS_ISO_STATE = "gse_state_14"
TORCH_ETHANOL_TANK_VENT = "gse_vlv_15"
TORCH_ETHANOL_TANK_VENT_STATE = "gse_state_15"
MARGIN_3 = "gse_vlv_16"
MARGIN_3_STATE = "gse_state_16"
TORCH_ETHANOL_MPV = "gse_vlv_17"
TORCH_ETHANOL_MPV_STATE = "gse_state_17"
TORCH_NITROUS_MPV = "gse_vlv_18"
TORCH_NITROUS_MPV_STATE = "gse_state_18"
TORCH_SPARK_PLUG = "gse_vlv_19"
TORCH_SPARK_PLUG_STATE = "gse_state_19"
PRESS_ISO = "gse_vlv_20"
PRESS_ISO_STATE = "gse_state_20"
FUEL_DOME_ISO = "gse_vlv_21"
FUEL_DOME_ISO_STATE = "gse_state_21"
OX_DOME_ISO = "gse_vlv_22"
OX_DOME_ISO_STATE = "gse_state_22"
OX_VENT = "gse_vlv_23"
OX_VENT_STATE = "gse_state_23"
FUEL_VENT = "gse_vlv_24"
FUEL_VENT_STATE = "gse_state_24"
VALVE_STATES = [
    OX_RETURN_LINE_STATE,
    OX_FILL_STATE,
    OX_PREVALVE_STATE,
    OX_DRAIN_STATE,
    OX_FILL_PURGE_STATE,
    OX_PRE_PRESS_STATE,
    MPV_PURGE_STATE,
    FUEL_PREPRESS_STATE,
    FUEL_PREVALVE_STATE,
    OX_MPV_STATE,
    FUEL_MPV_STATE,
    TORCH_FEEDLINE_PURGE_STATE,
    TORCH_ETHANOL_PRESS_ISO_STATE,
    TORCH_ETHANOL_TANK_VENT_STATE,
    MARGIN_3_STATE,
    TORCH_ETHANOL_MPV_STATE,
    TORCH_NITROUS_MPV_STATE,
    TORCH_SPARK_PLUG_STATE,
    PRESS_ISO_STATE,
    FUEL_DOME_ISO_STATE,
    OX_DOME_ISO_STATE,
    OX_VENT_STATE,
    FUEL_VENT_STATE,
]

NORMALLY_OPEN = [OX_VENT, FUEL_VENT, OX_MPV, FUEL_MPV]

### THERMOCOUPLES ###
OX_LIQUID_TC_1 = "gse_tc_1"
OX_LIQUID_TC_2 = "gse_tc_2"
OX_LIQUID_TC_3 = "gse_tc_3"
OX_ULLAGE_TC_1 = "gse_tc_4"
OX_FLOWMETER_TC = "gse_tc_5"
OX_RETURN_LINE_TC = "gse_tc_6"
REGEN_TC = "gse_tc_7"
FUEL_MANIFOLD_TC_1 = "gse_tc_8"
PRESS_SKIN_TC_1 = "gse_tc_9"
PRESS_SKIN_TC_2 = "gse_tc_10"
PRESS_SKIN_TC_3 = "gse_tc_11"
THERMOCOUPLES = [
    OX_LIQUID_TC_1,
    OX_LIQUID_TC_2,
    OX_LIQUID_TC_3,
    OX_ULLAGE_TC_1,
    OX_FLOWMETER_TC,
    OX_RETURN_LINE_TC,
    REGEN_TC,
    FUEL_MANIFOLD_TC_1,
    PRESS_SKIN_TC_1,
    PRESS_SKIN_TC_2,
    PRESS_SKIN_TC_3,
]

### LOAD CELLS ###
LOAD_CELL_1 = "gse_lc_1"
LOAD_CELL_2 = "gse_lc_2"
LOAD_CELL_3 = "gse_lc_3"
LOAD_CELLS = [LOAD_CELL_1, LOAD_CELL_2, LOAD_CELL_3]

ACKS = VALVE_STATES

CMDS = [OX_RETURN_LINE,
    OX_FILL,
    OX_PREVALVE,
    OX_DRAIN,
    OX_FILL_PURGE,
    OX_PRE_PRESS,
    MPV_PURGE,
    FUEL_PREPRESS,
    FUEL_PREVALVE,
    OX_MPV,
    FUEL_MPV,
    TORCH_FEEDLINE_PURGE,
    TORCH_ETHANOL_PRESS_ISO,
    TORCH_ETHANOL_TANK_VENT,
    MARGIN_3,
    TORCH_ETHANOL_MPV,
    TORCH_NITROUS_MPV,
    TORCH_SPARK_PLUG,
    PRESS_ISO,
    FUEL_DOME_ISO,
    OX_DOME_ISO,
    OX_VENT,
    FUEL_VENT,
    ]

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

FIRE_DURATION = 25

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
FUEL_TANK_1_DEQUE = deque()
FUEL_TANK_2_DEQUE = deque()
FUEL_TANK_3_DEQUE = deque()
OX_TANK_1_DEQUE = deque()
OX_TANK_2_DEQUE = deque()
OX_TANK_3_DEQUE = deque()
FUEL_TANK_1_SUM = 0
FUEL_TANK_2_SUM = 0
FUEL_TANK_3_SUM = 0
OX_TANK_1_SUM = 0
OX_TANK_2_SUM = 0
OX_TANK_3_SUM = 0

AVG_DICT = {
    FUEL_TANK_1: FUEL_TANK_1_DEQUE,
    FUEL_TANK_2: FUEL_TANK_2_DEQUE,
    FUEL_TANK_3: FUEL_TANK_3_DEQUE,
    OX_TANK_1: OX_TANK_1_DEQUE,
    OX_TANK_2: OX_TANK_2_DEQUE,
    OX_TANK_3: OX_TANK_3_DEQUE
}

SUM_DICT = {
    FUEL_TANK_1: FUEL_TANK_1_SUM,
    FUEL_TANK_2: FUEL_TANK_2_SUM,
    FUEL_TANK_3: FUEL_TANK_3_SUM,
    OX_TANK_1: OX_TANK_1_SUM,
    OX_TANK_2: OX_TANK_2_SUM,
    OX_TANK_3: OX_TANK_3_SUM
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
    ox_prepress = syauto.Valve(auto=auto, cmd=OX_PRE_PRESS, ack=OX_PRE_PRESS_STATE, normally_open=False)
    ox_dome_iso = syauto.Valve(auto=auto, cmd = OX_DOME_ISO, ack = OX_DOME_ISO_STATE, normally_open=False)
    ox_prevalve = syauto.Valve(auto=auto, cmd=OX_PREVALVE, ack=OX_PREVALVE_STATE, normally_open=False)
    ox_vent = syauto.Valve(auto=auto, cmd = OX_VENT, ack = OX_VENT_STATE, normally_open=True)
    ox_mpv = syauto.Valve(auto=auto, cmd = OX_MPV, ack = OX_MPV_STATE, normally_open=True)
    mpv_purge = syauto.Valve(auto=auto, cmd = MPV_PURGE, ack = MPV_PURGE_STATE, normally_open=False)
    fuel_prepress = syauto.Valve(auto=auto, cmd=FUEL_PREPRESS, ack=FUEL_PREPRESS_STATE, normally_open=False)
    fuel_prevalve = syauto.Valve(auto=auto, cmd=FUEL_PREVALVE, ack=FUEL_PREVALVE_STATE, normally_open=False)
    fuel_vent = syauto.Valve(auto=auto, cmd = FUEL_VENT, ack = FUEL_VENT_STATE, normally_open=True)
    fuel_mpv = syauto.Valve(auto=auto, cmd = FUEL_MPV, ack = FUEL_MPV_STATE, normally_open=True)
    fuel_dome_iso = syauto.Valve(auto=auto, cmd = FUEL_DOME_ISO, ack = FUEL_DOME_ISO_STATE, normally_open=False)
    press_iso = syauto.Valve(auto=auto, cmd = PRESS_ISO, ack = PRESS_ISO_STATE, normally_open=False)
    

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
            valves_to_potentially_open += [ox_vent]
        syauto.close_all(auto, valves_to_close)
        ans = input("would you like to open vents? y/n ")
        if ans == "y" or ans == "Y" or ans == "yes":
            syauto.open_all(auto, valves_to_potentially_open)

    def pressurize(auto: Controller) -> bool:
    
        averages = get_averages(auto, [OX_TANK_1, OX_TANK_2, OX_TANK_3, FUEL_TANK_1, FUEL_TANK_2, FUEL_TANK_3])
        ox_average = statistics.median([averages[OX_TANK_1], averages[OX_TANK_2], averages[OX_TANK_3]])
        ox_pre_press_open = auto[OX_PRE_PRESS_STATE]
        fuel_average = statistics.median([averages[FUEL_TANK_1], averages[FUEL_TANK_2], averages[FUEL_TANK_3]])
        fuel_pre_press_open = auto[FUEL_PREPRESS_STATE]

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
                fuel_ox_abort(auto, abort_fuel=True, abort_ox=False)

        if USING_OX:
            if ox_pre_press_open and (ox_average >= UPPER_OX_PRESSURE):
                print("ox repressurized")
                ox_prepress.close()

            if (not ox_pre_press_open) and (ox_average < LOWER_OX_PRESSURE):
                print("repressurizing ox")
                ox_prepress.open()    

            if ox_pre_press_open and ox_average > MAX_OX_PRESSURE:
                ox_prepress.close()
                print("ABORTING OX due to high pressure")
                fuel_ox_abort(auto, abort_fuel=False, abort_ox=True)

    def pressurize_while_user_input ():
            wait_thread = threading.Thread(target=wait_until_pressurized, args=(auto, pressurize))
            input_thread = threading.Thread(target=get_user_input)

            wait_thread.start()
            input_thread.start()

            wait_thread.join()
            input_thread.join()  

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
        opened_mpv = False
        opened_ox_mpv = False
        PROGRAM_STATE = "after ignition"
        try: # add thing to call pressuriez while user input if igniter does not work - going back to pressurize
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
            # igniter.open()
            time.sleep(1)
            print("5 deenergizing the igniter")
            # igniter.close()
            time.sleep(1)
            print("4")
            time.sleep(1)
            print("3")
            time.sleep(1)

            if (USING_FUEL and not USING_OX):
                print("2 Opening press and fuel dome isos")
                syauto.open_all(auto, [press_iso, fuel_dome_iso])

            elif (not USING_FUEL and USING_OX):
                print("2 Opening press and ox dome isos")
                syauto.open_all(auto, [press_iso, ox_dome_iso])

            else:
                print("2 Opening press and ox and fuel dome isos")
                syauto.open_all(auto, [press_iso, fuel_dome_iso, ox_dome_iso])

            time.sleep(1)
            print("1")
            time.sleep(1)

            if (USING_FUEL and not USING_OX):
                print("0")
                time.sleep(MPV_DELAY)
                print("Opening Fuel MPV")
                syauto.open_all(auto, [fuel_mpv])
                opened_fuel_mpv = True

            elif (not USING_FUEL and USING_OX):
                print("0 Opening Ox MPV")
                syauto.open_all(auto, [ox_mpv])
                opened_ox_mpv = True

            else:
                print("0 Opening Ox MPV")
                syauto.open_all(auto, [ox_mpv])
                opened_ox_mpv = True

                time.sleep(MPV_DELAY)
                print("Opening Fuel MPV")
                syauto.open_all(auto, [fuel_mpv])
                opened_fuel_mpv = True

            print(f"\nTerminating fire in")
            for i in range(FIRE_DURATION):
                print(f"{FIRE_DURATION - i}")
                time.sleep(1)

            print("Terminating fire")
            print("Closing MPVs")
            syauto.close_all(auto, [ox_mpv, fuel_mpv])
            time.sleep(2)
            print("Closing dome isos and openening vents and MPV purge")
            syauto.open_close_many_valves(auto, [ox_vent, fuel_vent, mpv_purge], [fuel_dome_iso, ox_dome_iso, press_iso])
            if opened_fuel_mpv:
                print("Closing fuel prevalve")
                fuel_prevalve.close()
            if opened_ox_mpv:
                print("Closing ox prevalve")
                ox_prevalve.close()
            time.sleep(5)
            print("Closing MPV purge")
            syauto.close_all(auto, [mpv_purge])
            print("\nFiring sequence has been completed nominally")
        except KeyboardInterrupt:
            # hotfire abort
            print("\nFiring sequence aborted, closing all valves and opening all vents")
            syauto.open_close_many_valves(auto,[fuel_vent, ox_vent],[fuel_dome_iso, ox_dome_iso, press_iso, fuel_mpv, ox_mpv])
            time.sleep(0.5)
            print("Opening MPV purge and closing prevalves")
            syauto.open_close_many_valves(auto, [mpv_purge], [fuel_prevalve, ox_prevalve])
            time.sleep(5)
            print ("Closing Torch feedline purge and MPV purge")
            syauto.close_all(auto, [mpv_purge])
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
            if (auto[FUEL_PREVALVE]):
                input("Fuel prevalve open, press enter to continue ")
            else:
                ans = input("Fuel prevalve NOT open, type 'bypass' to continue ")
                if (ans != 'bypass'):
                    print('closing program')
                    exit()
        elif (not USING_FUEL and USING_OX):
            if (auto[OX_PREVALVE]):
                input("Ox prevalve open, press enter to continue ")
            else:
                ans = input("Fuel prevalve NOT open, type 'bypass' to continue ")
                if (ans != 'bypass'):
                    print('closing program')
                    exit()
        else:
            if (auto[FUEL_PREVALVE_STATE] and auto[OX_PREVALVE_STATE]):
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
        syauto.close_all(auto, [press_iso, ox_dome_iso, fuel_dome_iso, press_iso, fuel_vent, ox_vent])

        time.sleep(1)
        
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
            exit()

        elif (PROGRAM_STATE == "after prepress before ignition"):
            pressurize_while_user_input()