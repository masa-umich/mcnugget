"""

TODO please note this does not actually work yet 3/21/24

### OVERVIEW ###

This autosequence pressurizes the PRESS_TANKS using regular 2K and Gooster

1. Set Starting State
    - Energize all normally_open
    - De-energize all normally_closed

2. 2k Bottle Equalization
    - Open and close press_fill to raise Press Tank Pressure at a constant rate of 65 psi/minute
        - done by opening press fill until Press Tank PT increases 65 psi from start pressure
        - next iteration targets target_pressure + 65 psi
        - The wait time between each press cycle (open/close) is 1 minute, measured from the start of the press_fill being opened 
    - Stop when 2K bottle and Press Tanks are within 10 psi of each other
    - Leave press_fill open
    - WAIT for confirmation

3. Pressurization with Gas Booster
    - Open gooster_fill
    - Open air_drive_iso_1
    - Open and close air_drive_iso_2 to raise psi at a 65 psi/min rate
    - Stop when Press Tanks reach TARGET_1 psi
    - Close air_drive_iso_1 and air_drive_iso_2
    - Close gooster_fill
    - Close press_fill
    - WAIT for confirmation

---
### IMPORTANT INFO ###

When measuring PRESS_TANKS, we measure from 3 PTs and 4 TCs.

The overall pressure of the PRESS_TANKS is considered to be equal to the median of the 3 readings

Any of these conditions will trigger an abort
    - 2/3 PTs reading an invalid value (below -100 or above MAWP)
    - 3/4 TCs reading an invalid temperature (above 140)

auto.wait_until(lambda function) is a function which returns when the defined lambda returns TRUE

We will use the runsafe_press_tank_fill(TARGET) function as our lambda, which will check
    - whether 2/3 PTs read invalid pressures (> MAX_PRESSURE, < -100) -> ABORT
    - whether 3/4 TCs read invalid temperatures (> MAX_TEMPERATURE) -> ABORT
    - whether the median PT is above the target temperature -> RETURN

This will allow us to safely pressurize in increments. The custom pressurize function will also
    require a manual confirm if any of the TCs read a temperature above 60 C.

An interrupt command (ctrl + C) will cause all Valves and Vents to CLOSE. Must hit REDS to depressurize system
All aborts also currently (3/21/24) just close all valves.

---
### VALVES LIST ###

For this test, the only valves we will need to control are:

    ---VALVES---
    Press Fill Valve
    Air Drive ISO 1
    Air Drive ISO 2
    Gas Booster Fill

    ---VENTS---
    Press Vent

    ---PT CHANNELS---
    Press Tank PT 1
    Press Tank PT 2
    Press Tank PT 3
    Press Tank Supply

    ---TC CHANNELS---
    Press Tank TC 1
    Press Tank TC 2
    Press Tank TC 3
    Press Tank TC 4

As such, all other valves/vents have been left out! Channel names are left in case they change the day of.

"""

import time
import synnax as sy
from synnax.control.controller import Controller
import syauto
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

# change names and numbers to match the actual channels
# valve names to channel names
v1_in = "gse_doa_1"
v1_out = "gse_doc_1"
v2_in = "gse_doa_2"
v2_out = "gse_doc_2"
v3_in = "gse_doa_3"
v3_out = "gse_doc_3"
v4_in = "gse_doa_4"
v4_out = "gse_doc_4"
v5_in = "gse_doa_5"
v5_out = "gse_doc_5"
v6_in = "gse_doa_6"
v6_out = "gse_doc_6"
v7_in = "gse_doa_7"
v7_out = "gse_doc_7"
v8_in = "gse_doa_8"
v8_out = "gse_doc_8"
v9_in = "gse_doa_9"
v9_out = "gse_doc_9"
v10_in = "gse_doa_10"
v10_out = "gse_doc_10"
v11_in = "gse_doa_11"
v11_out = "gse_doc_11"
v12_in = "gse_doa_12"
v12_out = "gse_doc_12"
v13_in = "gse_doa_13"
v13_out = "gse_doc_13"
v14_in = "gse_doa_14"
v14_out = "gse_doc_14"
v15_in = "gse_doa_15"
v15_out = "gse_doc_15"
v16_in = "gse_doa_16"
v16_out = "gse_doc_16"
v17_in = "gse_doa_17"
v17_out = "gse_doc_17"
v18_in = "gse_doa_18"
v18_out = "gse_doc_18"
v19_in = "gse_doa_19"
v19_out = "gse_doc_19"
v20_in = "gse_doa_20"
v20_out = "gse_doc_20"
v21_in = "gse_doa_21"
v21_out = "gse_doc_21"
v22_in = "gse_doa_22"
v22_out = "gse_doc_22"
v23_in = "gse_doa_23"
v23_out = "gse_doc_23"
v24_in = "gse_doa_24"
v24_out = "gse_doc_24"
# v25_in = "gse_doa_25"
# v25_out = "gse_doc_25"

# sensor names for PTs
A1 = "gse_ai_1"
A2 = "gse_ai_2"
A3 = "gse_ai_3"
A4 = "gse_ai_4"
A5 = "gse_ai_5"
A6 = "gse_ai_6"
A7 = "gse_ai_7"
A8 = "gse_ai_8"
A9 = "gse_ai_9"
A10 = "gse_ai_10"
A11 = "gse_ai_11"
A12 = "gse_ai_12"
A13 = "gse_ai_13"
A14 = "gse_ai_14"
A15 = "gse_ai_15"
A16 = "gse_ai_16"
A17 = "gse_ai_17"
A18 = "gse_ai_18"
A19 = "gse_ai_19"
A20 = "gse_ai_20"
A21 = "gse_ai_21"
A22 = "gse_ai_22"
A23 = "gse_ai_23"
A24 = "gse_ai_24"
A25 = "gse_ai_25"
A26 = "gse_ai_26"
A27 = "gse_ai_27"
A28 = "gse_ai_28"
A29 = "gse_ai_29"
A30 = "gse_ai_30"
A31 = "gse_ai_31"
A32 = "gse_ai_32"
A33 = "gse_ai_33"
A34 = "gse_ai_34"
A35 = "gse_ai_35"
A36 = "gse_ai_36"

# sensor names for TCs
TC1 = "gse_tc_1"  # gse_ai_65
TC2 = "gse_tc_2"  # gse_ai_66
TC3 = "gse_tc_3"  # gse_ai_67
TC4 = "gse_tc_4"  # gse_ai_68
TC5 = "gse_tc_5"  # gse_ai_70
TC6 = "gse_tc_6"  # gse_ai_71
TC7 = "gse_tc_7"  # gse_ai_72
TC8 = "gse_tc_8"  # gse_ai_73
TC9 = "gse_tc_9"  # gse_ai_74
TC10 = "gse_tc_10"  # gse_ai_75
TC11 = "gse_tc_11"  # gse_ai_76
TC12 = "gse_tc_12"  # gse_ai_77
TC13 = "gse_tc_13"  # gse_ai_78
TC14 = "gse_tc_14"  # gse_ai_79
TC15 = "gse_tc_15"  # gse_ai_80
TC16 = "gse_tc_16"  # gse_ai_81

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

MAX_PRESS_TANK_PRESSURE = 4500  # psi
MAX_PRESS_TANK_TEMP = 60  # celsius. ichiro edit since stuff should be in C, not cringe F. Thermocouple output is in C right?
ALMOST_MAX_PRESS_TANK_TEMP = 50  # celsius

PRESS_TARGET = 3700  # psi
PRESS_INC = 65  # psi/min # ichiro edit
PRESS_DELAY = 60  # seconds # ichiro edit

PRESS_TANK_PT_1 = A22
PRESS_TANK_PT_2 = A24
PRESS_TANK_PT_3 = A26

PRESS_TANK_TC_1 = TC8
PRESS_TANK_TC_2 = TC9
PRESS_TANK_TC_3 = TC10
PRESS_TANK_TC_4 = TC11

PRESS_TANK_SUPPLY = A23

# this variable defines how many samples should be averaged for PT or TC data
RUNNING_MEDIAN_SIZE = 100  # samples - at 200Hz this means every 1/2 second

# This section implements a running average for the PT sensors to mitigate the effects of noise
PRESS_TANK_PT_1_DEQUE = deque()
PRESS_TANK_PT_2_DEQUE = deque()
PRESS_TANK_PT_3_DEQUE = deque()

PRESS_TANK_TC_1_DEQUE = deque()
PRESS_TANK_TC_2_DEQUE = deque()
PRESS_TANK_TC_3_DEQUE = deque()
PRESS_TANK_TC_4_DEQUE = deque()

PRESS_TANK_PT_1_SUM = 0
PRESS_TANK_PT_2_SUM = 0
PRESS_TANK_PT_3_SUM = 0

PRESS_TANK_TC_1_SUM = 0
PRESS_TANK_TC_2_SUM = 0
PRESS_TANK_TC_3_SUM = 0
PRESS_TANK_TC_4_SUM = 0

AVG_DICT = {
    PRESS_TANK_PT_1: PRESS_TANK_PT_1_DEQUE,
    PRESS_TANK_PT_2: PRESS_TANK_PT_2_DEQUE,
    PRESS_TANK_PT_3: PRESS_TANK_PT_3_DEQUE,
    PRESS_TANK_TC_1: PRESS_TANK_TC_1_DEQUE,
    PRESS_TANK_TC_2: PRESS_TANK_TC_2_DEQUE,
    PRESS_TANK_TC_3: PRESS_TANK_TC_3_DEQUE,
    PRESS_TANK_TC_4: PRESS_TANK_TC_4_DEQUE
}

SUM_DICT = {
    PRESS_TANK_PT_1: PRESS_TANK_PT_1_SUM,
    PRESS_TANK_PT_2: PRESS_TANK_PT_2_SUM,
    PRESS_TANK_PT_3: PRESS_TANK_PT_3_SUM,
    PRESS_TANK_TC_1: PRESS_TANK_TC_1_SUM,
    PRESS_TANK_TC_2: PRESS_TANK_TC_2_SUM,
    PRESS_TANK_TC_3: PRESS_TANK_TC_3_SUM,
    PRESS_TANK_TC_4: PRESS_TANK_TC_4_SUM
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

print("Starting autosequence")
with client.control.acquire(name="Press and Fill Autos", write=WRITE_TO, read=READ_FROM) as auto:

    ###     DECLARES THE VALVES WHICH WILL BE USED     ###

    air_drive_ISO_1 = syauto.Valve(
        auto=auto, cmd=v3_out, ack=v3_in, normally_open=False)
    air_drive_ISO_2 = syauto.Valve(
        auto=auto, cmd=v4_out, ack=v4_in, normally_open=False)
    
    gas_booster_fill = syauto.Valve(
        auto=auto, cmd=v20_out, ack=v20_in, normally_open=False)
    press_fill = syauto.Valve(auto=auto, cmd=v23_out,
                              ack=v23_in, normally_open=False)
    
    # press vent is normally open
    press_vent = syauto.Valve(auto=auto, cmd=v18_out,
                              ack=v18_in, normally_open=True)

    all_vents = [press_vent]
    all_valves = [air_drive_ISO_1, air_drive_ISO_2, gas_booster_fill, press_fill]

    def runsafe_press_tank_fill(partial_target: float):
        # this function returns True if
            # the partial_target has been reached
            # an ABORT was triggered
        # if an ABORT was triggered, it also closes ALL_VALVES and ALL_VENTS

        # this computes PT and TC values with a running average, see compute_medians
        readings = get_averages(auto, [PRESS_TANK_PT_1, PRESS_TANK_PT_2, PRESS_TANK_PT_3, PRESS_TANK_TC_1, PRESS_TANK_TC_2, PRESS_TANK_TC_3, PRESS_TANK_TC_4])

        # aliases each reading to a meaningful value
        # READINGS aka PTs_and_TCs must be in the same order or this will be incorrect!
        [pt1, pt2, pt3, ] = [readings[PRESS_TANK_PT_1], 
                                               readings[PRESS_TANK_PT_2], 
                                               readings[PRESS_TANK_PT_3], 
                                               readings[PRESS_TANK_TC_1], 
                                               readings[PRESS_TANK_TC_2], 
                                               readings[PRESS_TANK_TC_3], 
                                               readings[PRESS_TANK_TC_4]]

        pts_below_min = 0
        pts_above_max = 0
        for pt in [pt1, pt2, pt3]:
            if pt < -100:
                pts_below_min += 1
            if pt > MAX_PRESS_TANK_PRESSURE:
                pts_above_max += 1

        tcs_above_max = 0
        for tc in [tc1, tc2, tc3, tc4]:
            if tc > MAX_PRESS_TANK_TEMP:
                tcs_above_max += 1

        if pts_above_max >= 2:
            print("ABORTING due to 2+ PTs EXCEEDING MAX_PRESS_TANK_PRESSURE")
            syauto.close_all(auto=auto, valves=(all_valves + all_vents))
            input("Press any key to continue pressurizing, or ctrl-c to execute abort sequence")

        if pts_below_min >= 2:
            print("ABORTING due to 2+ PTs BELOW -100 psi")
            syauto.close_all(auto=auto, valves=(all_valves + all_vents))
            input("Press any key to continue pressurizing, or ctrl-c to execute abort sequence")
        
        if tcs_above_max >= 3:
            print("ABORTING due to 3+ TCs EXCEEDING MAX_PRESS_TANK_TEMP")
            syauto.close_all(auto=auto, valves=(all_valves + all_vents))
            input("Press any key to continue pressurizing, or ctrl-c to execute abort sequence")

        if statistics.median([pt1, pt2, pt3]) >= partial_target:
            print(f"press tanks have reached {partial_target}")
            return True


    def press_phase_1():
        # this function uses the runsafe_press_tank_fill() function to equalize pressure between 2K supply and press tanks
        # it returns when the PRESS_TANKs pressure is within 10psi of the 2K bottle supply
        partial_target = 0
        while True:
            press_supply = compute_medians([PRESS_TANK_SUPPLY])[0]
            partial_target += PRESS_INC

            # this is the only way for the function to return 
            # if for some reason PRESS_TANK_SUPPLY and PRESS_TANKS do not converge, you will enter a loop
            if abs(partial_target - press_supply) < 30:
                print("PRESS_TANKS pressure is sufficiently close to 2K supply")
                print("Leaving press_fill open")
                press_fill.open()
                return
            

            # this triggers a manual confirm if median TC is above ALMOST_MAX_PRESS_TANK_TEMP 
                # without changing the running median for TCs
            try:
                tc_readings = []
                for tc in [PRESS_TANK_TC_1, PRESS_TANK_PT_2, PRESS_TANK_TC_3, PRESS_TANK_TC_4]:
                        tc_readings.append(statistics.median(median_arrs[tc]))
                        tc_readings.append(0)
                median_tc = statistics.median(tc_readings)

                if median_tc > ALMOST_MAX_PRESS_TANK_TEMP:
                    input(f"Press Tank median temperature is above {ALMOST_MAX_PRESS_TANK_TEMP}, press any key to confirm press")

            except statistics.StatisticsError as e:
                print("no data for TC checks; skipping this iteration")

            # Measure time press_fill is open so that we keep a constant 60 psi/minute press rate
            # ex: as pressures get closer to equalizing, press fill is held open for longer, and the PRESS_DELAY actually needs to start decreasing
            #     therefore we want to subtract the time it took to press 
            # opens press_fill until partial_target is reached or abort occurs
            press_start_time = sy.TimeStamp.now()  # ichiro edit

            press_fill.open()
            auto.wait_until(lambda c: runsafe_press_tank_fill(partial_target=partial_target))
            press_fill.close()

            press_end_time = sy.TimeStamp.now() # ichiro edit
            time_to_press = press_end_time - press_start_time # ichiro edit

            # sleeps for 60 seconds minus the time it took to press
            time.sleep(PRESS_DELAY - time_to_press.seconds) # ichiro edit
            

    def press_phase_2():
        # this function completes steps 2-4 see section 3 of overview
        # starts at partial_target = current pressure + increment
        partial_target = statistics.median(compute_medians([PRESS_TANK_PT_1, PRESS_TANK_PT_2, PRESS_TANK_PT_3]))
        # partial_target += PRESS_INC   # pretty sure this would cause us to increase target by 2x press_inc before opening air_drive_iso_2
        while True:
            partial_target += PRESS_INC

            # this is the only way for the function to return 
            # if for some reason PRESS_TANK_SUPPLY and PRESS_TANKS do not converge, you will enter a loop
            if partial_target >= PRESS_TARGET:
                print(f"PRESS_TANKS pressure has reached {PRESS_TARGET}")
                syauto.close_all(auto=auto, valves=[air_drive_ISO_1, air_drive_ISO_2])
                print("Both air_drive_iso valves are closed")
                return
            

            # this triggers a manual confirm if median TC is above ALMOST_MAX_PRESS_TANK_TEMP 
                # without changing the running median for TCs
            try:
                tc_readings = []
                for tc in [PRESS_TANK_TC_1, PRESS_TANK_PT_2, PRESS_TANK_TC_3, PRESS_TANK_TC_4]:
                        tc_readings.append(statistics.median(median_arrs[tc]))
                        tc_readings.append(0)
                median_tc = statistics.median(tc_readings)

                if median_tc > ALMOST_MAX_PRESS_TANK_TEMP:
                    input(f"Press Tank median temperature is above {ALMOST_MAX_PRESS_TANK_TEMP}, press any key to confirm press")

            except statistics.StatisticsError as e:
                print("no data for TC checks; skipping this iteration")

            # Measure time press_fill is open so that we keep a constant 60 psi/minute press rate
            # ex: as pressures get closer to equalizing, press fill is held open for longer, and the PRESS_DELAY actually needs to start decreasing
            #     therefore we want to subtract the time it took to press 
            # opens press_fill until partial_target is reached or abort occurs
            press_start_time = sy.TimeStamp.now()  # ichiro edit

            # opens air_drive_iso valves until partial_target is reached or abort occurs
            syauto.open_all(auto=auto, valves=[air_drive_ISO_2])
            auto.wait_until(lambda c: runsafe_press_tank_fill(partial_target=partial_target))
            syauto.close_all(auto=auto, valves=[air_drive_ISO_2])

            press_end_time = sy.TimeStamp.now()  # ichiro edit

            time_to_press = press_end_time - press_start_time # ichiro edit

            time.sleep(PRESS_DELAY - time_to_press.seconds) # ichiro edit


    ###     RUNS ACTUAL AUTOSEQUENCE         ###
    try:
        input("running the wrong autosequence dawg, this shit aint ready")
        print("beginning other testing")
        # print(auto[PRESS_TANK_SUPPLY])
        print("finished other testing")

        # starts by closing all valves and closing all vents
        print("Starting Press Fill Autosequence. Setting initial system state.")
        syauto.close_all(auto, all_valves + all_vents)
        time.sleep(1)

        print("PHASE 1: 2K Bottle Equalization")
        print(
            f"pressurizing PRESS_TANKS using {press_fill.name} until approximately equal with 2K supply")
        press_phase_1()

        print("Pressurization phase 1 complete")
        time.sleep(5) # add in to give operators some time to breathe
        #press_fill.close(), not needed since we are theoretically equalized
        input("Press any key to continue")

        print("PHASE 2: Pressurization with Gas Booster")

        print("opening gas_booster_fill and air_drive_ISO_1")
        gas_booster_fill.open()
        air_drive_ISO_1.open()
        press_phase_2()

        print("closing gas_booster_fill and air_drive_ISO_1")
        gas_booster_fill.close()

        print("Pressurization phase 2 complete")
        input("Press any key to continue")

        print("Test complete. Safing System")
        syauto.close_all(auto=auto, valves=(all_vents + all_valves))
        print("Valves and Vents closed ")

        #Creating a range inside autosequences
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Press Fill",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

    except KeyboardInterrupt as e:
        # Handle Ctrl+C interruption
        if str(e) == "Interrupted by user.":
            print("Test interrupted. Safing System")
            syauto.close_all(auto=auto, valves=(all_vents + all_valves))

    time.sleep(60)
