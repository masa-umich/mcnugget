"""

### OVERVIEW ###

This autosequence pressurizes the PRESS_TANKS using regular 2K and Gooster

Once you run this autosequence, you will be prompted to specify the type of test:
- HOTFIRE
    - Connects to synnax.masa.engin.umich.edu
    - Uses the Press Delay intended for Hot Fire

- COLDFLOW
    - Connects to synnax.masa.engin.umich.edu
    - Uses the Press Delay intended for Cold Flow

- SIM
    - Connects to localhost
    - Uses a shorter Press Delay to keep sims running fast 

After initializing the client and reference variables, the autosequence will:

1. Set Starting State
    - Energize all normally_open
    - De-energize all normally_closed
    
2. PHASE 1: 2k Bottle Equalization
    - Open and close press_fill to raise psi at target rate
    - Stop when 2K bottle and Press Tanks are within 80 psi of each other
    - Leave press_fill open
    - WAIT for confirmation

3. PHASE 2: Pressurization with Gas Booster
    - Open gooster_fill
    - Open air_drive_iso_1
    - Open and close air_drive_iso_2 to raise psi at target rate
    - Stop when Press Tanks reach press_target psi
        - if it takes more then Press Delay time to pressurize, will prompt user to continue or end
    - Close air_drive_iso_1 and air_drive_iso_2
    - Close gooster_fill
    - Close press_fill

"""

import time
import synnax as sy
from synnax.control.controller import Controller
import syauto
import statistics
from collections import deque

MAX_PRESS_TANK_PRESSURE = 4400  # psi
MAX_PRESS_TANK_TEMP = 60  # celsius
ALMOST_MAX_PRESS_TANK_TEMP = 50  # celsius

PRESS_TARGET = 500  # psi
REPRESS_TARGET = 400 #psi
PRESS_INC_1 = 50  # psi/min
PRESS_INC_2 = 50  # psi/min
# press tank will pressurize at a rate of PRESS_INC / PRESS_DELAY psi/second

# this variable defines how many samples should be averaged for PT or TC data
RUNNING_MEDIAN_SIZE = 50  # samples - at 200Hz this means every 1/2 second

# TODO: Change Delays as Necessary 
COLDFLOW_PRESS_DELAY = 60

HOTFIRE_PRESS_DELAY = 100

SIM_PRESS_DELAY = COLDFLOW_PRESS_DELAY

PRESS_FACTOR = 1

print("Simulation mode")
# this connects to a local synnax simulation server
client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)
PRESS_DELAY = SIM_PRESS_DELAY
PRESS_FACTOR = 1/100

PRESS_FILL_EQUALIZED = False

PRESS_PT_1 = "gse_ai_26"
PRESS_PT_2 = "gse_ai_24"
PRESS_PT_3 = "gse_ai_22"
PRESS_TANK_SUPPLY = "gse_ai_23"

AIR_DRIVE_ISO_1_CMD = "gse_doc_5"
AIR_DRIVE_ISO_1_ACK = "gse_doa_5"
AIR_DRIVE_ISO_2_CMD = "gse_doc_4"
AIR_DRIVE_ISO_2_ACK = "gse_doa_4"
GAS_BOOSTER_FILL_CMD = "gse_doc_20"
GAS_BOOSTER_FILL_ACK = "gse_doa_20"
PRESS_FILL_CMD = "gse_doc_23"
PRESS_FILL_ACK = "gse_doa_23"
PRESS_VENT_CMD = "gse_doc_18"
PRESS_VENT_ACK = "gse_doa_18"

CMDS = [AIR_DRIVE_ISO_1_CMD, AIR_DRIVE_ISO_2_CMD, GAS_BOOSTER_FILL_CMD, PRESS_FILL_CMD, PRESS_VENT_CMD]
ACKS = [AIR_DRIVE_ISO_1_ACK, AIR_DRIVE_ISO_2_ACK, GAS_BOOSTER_FILL_ACK, PRESS_FILL_ACK, PRESS_VENT_ACK]
PTS = [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3, PRESS_TANK_SUPPLY]

WRITE_TO = []
READ_FROM = []
for cmd in CMDS:
    WRITE_TO.append(cmd)
for ack in ACKS:
    READ_FROM.append(ack)
for pt in PTS:
    READ_FROM.append(pt)

start = sy.TimeStamp.now()
press_start_time = time.time()

# Running average implementation
PRESS_PT_1_DEQUE = deque()
PRESS_PT_2_DEQUE = deque()
PRESS_PT_3_DEQUE = deque()
PRESS_TANK_SUPPLY_DEQUE = deque()

PRESS_PT_1_SUM = 0
PRESS_PT_2_SUM = 0
PRESS_PT_3_SUM = 0
PRESS_TANK_SUPPLY_SUM = 0

AVG_DICT = {
    PRESS_PT_1: PRESS_PT_1_DEQUE,
    PRESS_PT_2: PRESS_PT_2_DEQUE,
    PRESS_PT_3: PRESS_PT_3_DEQUE,
    PRESS_TANK_SUPPLY: PRESS_TANK_SUPPLY_DEQUE
}

SUM_DICT = {
    PRESS_PT_1: PRESS_PT_1_SUM,
    PRESS_PT_2: PRESS_PT_2_SUM,
    PRESS_PT_3: PRESS_PT_3_SUM,
    PRESS_TANK_SUPPLY: PRESS_TANK_SUPPLY_SUM
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

def check_for_repress() -> bool:
    print("checking for repress")
    readings = get_averages(auto, [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3])
    if statistics.median(readings[pt] for pt in [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3]) <= REPRESS_TARGET:
        return True

def runsafe_press_tank_fill(partial_target: float, press_start_time_, phase_2=False):
    # this function returns True if
        # the partial_target has been reached
        # an ABORT was triggered
    # if an ABORT was triggered, it also closes ALL_VALVES and ALL_VENTS

    # this computes PT and TC values with a running average, see compute_medians
    readings = get_averages(auto, [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3, PRESS_TANK_SUPPLY])

    [pt1, pt2, pt3] = [ readings[PRESS_PT_1], 
                        readings[PRESS_PT_2], 
                        readings[PRESS_PT_3] ]

    pts_below_min = 0
    pts_above_max = 0
    for pt in [pt1, pt2, pt3]:
        if pt < -100:
            pts_below_min += 1
        if pt > MAX_PRESS_TANK_PRESSURE:
            pts_above_max += 1

    if pts_above_max >= 2:
        print("ABORTING due to 2+ PTs EXCEEDING MAX_PRESS_TANK_PRESSURE")
        syauto.open_close_many_valves(auto=auto, valves_to_open=[press_vent], valves_to_close=[air_drive_ISO_1, air_drive_ISO_2, gas_booster_fill, press_fill])
        input("Press any key to continue pressurizing, or ctrl-c to execute abort sequence")

    if pts_below_min >= 2:
        print("ABORTING due to 2+ PTs BELOW -100 psi")
        syauto.close_all(auto=auto, valves=[air_drive_ISO_1, air_drive_ISO_2, gas_booster_fill, press_fill, press_vent])
        input("Press any key to continue pressurizing, or ctrl-c to execute abort sequence")

    if statistics.median([pt1, pt2, pt3]) >= partial_target:
        return True
    
    press_diff = statistics.median([pt1, pt2, pt3]) - get_averages(auto, [PRESS_TANK_SUPPLY])[PRESS_TANK_SUPPLY]

    if (not phase_2) and (abs(press_diff) < 80 or press_diff > 0):
        # PRESS_FILL_EQUALIZED = True  # causes python to explode bc scope is stupid
        print("press tanks and 2k supply have been equalized")
        return True
    
    if (time.time() - press_start_time_) > PRESS_DELAY:
        answer = input(f"unable to pressurize to target in {PRESS_DELAY} seconds, input n to stop")
        if answer == "n":
            return True
        press_start_time_ = time.time()

    # stops if target pressure is reached and repressurizes at REPRESS_TARGET if needed
    if statistics.median([pt1, pt2, pt3]) >= PRESS_TARGET:

            
        print(f"press tanks have reached {PRESS_TARGET} psi, closing air drive ISO 2")
        syauto.close_all(auto=auto, valves=[air_drive_ISO_2])
        print (f"Air drive ISO 2 closed, will repressurize at {REPRESS_TARGET}")
        auto.wait_until(check_for_repress)
        syauto.open_all(auto=auto, valves=[air_drive_ISO_2])

def press_phase_1():
    # this function uses the runsafe_press_tank_fill() function to equalize pressure between 2K supply and press tanks
    times_ran = 0
    # it returns when the PRESS_TANKs pressure is within 10psi of the 2K bottle supply
    p_avgs = get_averages(auto, [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3])
    partial_target = statistics.median([p_avgs[PRESS_PT_1], p_avgs[PRESS_PT_2], p_avgs[PRESS_PT_3]])
    while True:
        current_pressure = statistics.median([p_avgs[PRESS_PT_1], p_avgs[PRESS_PT_2], p_avgs[PRESS_PT_3]])

        press_supply = get_averages(auto, [PRESS_TANK_SUPPLY])[PRESS_TANK_SUPPLY]
        p_avgs = get_averages(auto, [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3])
        press_tanks = statistics.median([p_avgs[PRESS_PT_1], p_avgs[PRESS_PT_2], p_avgs[PRESS_PT_3]])
        if times_ran < 4:
            partial_target += PRESS_INC_1
        else:
            partial_target += PRESS_INC_2

        # this is the only way for the function to return 
        # if  PRESS_TANK_SUPPLY does not eventually reach PRESS_TANKS pressure, you will enter a loop
        print(f"press tanks: {round(press_tanks, 2)}, 2k supply: {round(press_supply, 2)}")
        if (abs(press_tanks - press_supply) < 80 or press_tanks > press_supply):
            return

        # Open press_fill until partial_target is reached and ensure we do not exceed maximum rate
        press_start_time = time.time()

        press_fill.open()
        print(f"pressurizing from {round(current_pressure, 2)} to {round(partial_target, 2)}")
        auto.wait_until(lambda c: runsafe_press_tank_fill(partial_target=partial_target, press_start_time_=press_start_time))
        press_fill.close()

        time_pressed = time.time() - press_start_time 

        # sleeps for 60 seconds minus the time it took to press
        print(f"sleeping for {round(max(PRESS_FACTOR * (PRESS_DELAY - time_pressed), 0), 2)} seconds")
        time.sleep(max(PRESS_FACTOR * (PRESS_DELAY - time_pressed), 0))
        times_ran += 1
        

def press_phase_2():
    # this function completes steps 2-4 see section 3 of overview
    PRESS_FILL_EQUALIZED = True
    avgs = get_averages(auto, [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3])
    partial_target = statistics.median([avgs[PRESS_PT_1], avgs[PRESS_PT_2], avgs[PRESS_PT_3]])

    print("leaving air_drive_iso_1 open")
    air_drive_ISO_1.open()

    while True:
        avgs = get_averages(auto, [PRESS_PT_1, PRESS_PT_2, PRESS_PT_3])
        current_press = statistics.median([avgs[PRESS_PT_1], avgs[PRESS_PT_2], avgs[PRESS_PT_3]])

        partial_target += PRESS_INC_2
        print(f"current pressure: {round(current_press, 2)}, pressurizing to {round(partial_target, 2)}")

        press_start_time = time.time()

        # opens air_drive_iso valves until partial_target is reached or abort occurs
        syauto.open_all(auto=auto, valves=[air_drive_ISO_2])
        auto.wait_until(lambda c: runsafe_press_tank_fill(partial_target=partial_target, press_start_time_=time.time(), phase_2=True))
        syauto.close_all(auto=auto, valves=[air_drive_ISO_2])

        time_pressed = time.time() - press_start_time

        # sleeps for 60 seconds minus the time it took to press
        print(f"sleeping for {round(max(PRESS_FACTOR * (PRESS_DELAY - time_pressed), 0), 2)} seconds")
        time.sleep(max(PRESS_FACTOR * (PRESS_DELAY - time_pressed), 0))

with client.control.acquire(name="Press and Fill Autos", write=WRITE_TO, read=READ_FROM, write_authorities=180) as auto:
    air_drive_ISO_1 = syauto.Valve(
        auto=auto, cmd=AIR_DRIVE_ISO_1_CMD, ack=AIR_DRIVE_ISO_1_ACK, normally_open=False)
    air_drive_ISO_2 = syauto.Valve(
        auto=auto, cmd=AIR_DRIVE_ISO_2_CMD, ack=AIR_DRIVE_ISO_2_ACK, normally_open=False)
    gas_booster_fill = syauto.Valve(
        auto=auto, cmd=GAS_BOOSTER_FILL_CMD, ack=GAS_BOOSTER_FILL_ACK, normally_open=False)
    press_fill = syauto.Valve(auto=auto, cmd=PRESS_FILL_CMD,
                              ack=PRESS_FILL_ACK, normally_open=False)
    
    press_vent = syauto.Valve(auto=auto, cmd=PRESS_VENT_CMD,
                              ack=PRESS_VENT_ACK, normally_open=True)

    all_vents = [press_vent]
    all_valves = [air_drive_ISO_1, air_drive_ISO_2, gas_booster_fill, press_fill]

    ###     RUNS ACTUAL AUTOSEQUENCE         ###
    try:
        # starts by closing all valves and closing all vents
        print("Starting Press Fill Autosequence. Setting initial system state.")
        syauto.close_all(auto, [air_drive_ISO_1, air_drive_ISO_2, gas_booster_fill, press_fill, press_vent])
        time.sleep(1)

        # print("PHASE 1: 2K Bottle Equalization")
        # print(f"pressurizing PRESS_TANKS using press_fill until approximately equal with 2K supply")
        # press_phase_1()
        # print("PHASE 1 complete")

        time.sleep(1)
        print("Leaving press_fill open")
        press_fill.open()

        input("Press any key to continue to PHASE 2")

        print("PHASE 2: Pressurization with Gas Booster")
        print("opening gas_booster_fill and air_drive_ISO_1")
        gas_booster_fill.open()
        air_drive_ISO_1.open()
        press_phase_2()


    except KeyboardInterrupt as e:
        # Handle Ctrl+C interruption
            # if str(e) == "Interrupted by user.":  # needed for windows systems?
        print("Manual abort, safing system")
        print("Closing all valves and vents")
        syauto.close_all(auto=auto, valves=(all_vents + all_valves))

        response = input("Input 'y' to open press vent: ")
        if(response == "y"):
            press_vent.open()
            print("press vent opened")

        print("Creating range for data processing")
        #Creating a range inside autosequences
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Press Fill",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

    print("ctrl-c to terminating autosequence")
    time.sleep(60)