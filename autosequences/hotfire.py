"""

### OVERVIEW ###

This autosequence combines the processes of pre_press.py and reg_fire.py.

Software controls ground systems, avionics takes over MPVs after handoff.

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

    4. Handoff to avionics for MPV control
        - Connection will be lost after MPV opening

    5. Close Valves (if still connected)
    - Close all the valves opened in step 3
    - Open FUEL_VENT and OX_LOW_FLOW_VENT and PRESS_VENT

X. Abort
    - The only conditions which will trigger an abort:
                    - 2/3 PTs reading above maximum pressure for OX_TANK or FUEL_TANK
            - Manual ctrl-c

"""

from autosequences import syauto
import time
from synnax.control.controller import Controller
import synnax as sy
import statistics
from collections import deque
from datetime import datetime, timedelta

#Prompts for user input as to whether we want to run a simulation or run an actual test
#If prompted to run a coldflow test, we will connect to the MASA remote server and have a delay of 60 seconds
real_test = False
mode = input("Enter 'real' for coldflow/hotfire or 'sim' to run a simulation: ")
if(mode == "real" or mode == "Real" or mode == "REAL"):
    real_test = True
    print("Testing mode")

#If prompted to run a simulation, the delay will be 1 second and we will connect to the synnax simulation server
elif mode == "sim" or mode == "Sim" or mode == "SIM" or mode == "":
    real_test = False
    print("Simulation mode")

else:
    print("Bestie what are you trying to do? If it's a typo, just try again, we're gonna close to program for now though <3")
    exit()

client = sy.Synnax()

USING_FUEL = True

USING_OX = True

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

# MPV and igniter channels - controlled by avionics after handoff
OX_MPV_CMD = "gse_doc_6"
OX_MPV_ACK = "gse_doa_6"
FUEL_MPV_CMD = "gse_doc_24"
FUEL_MPV_ACK = "gse_doa_24"
IGNITER_CMD = "gse_doc_25"
IGNITER_ACK = "gse_doa_25"

# handoff channels - avionics team needs to implement these
AVIONICS_HANDOFF_CMD = "avionics_handoff_cmd"
AVIONICS_HANDOFF_ACK = "avionics_handoff_ack"
AVIONICS_STATUS_CMD = "avionics_status_cmd"

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
        FUEL_FEEDLINE_PURGE_ACK, OX_FEEDLINE_PURGE_ACK]
CMDS = [FUEL_PREVALVE_CMD, OX_PREVALVE_CMD, FUEL_PRESS_ISO_CMD, OX_PRESS_ISO_CMD, OX_DOME_ISO_CMD, 
        FUEL_VENT_CMD, OX_LOW_FLOW_VENT_CMD, PRESS_VENT_CMD, FUEL_PRE_PRESS_CMD, OX_PRE_PRESS_CMD,
        FUEL_FEEDLINE_PURGE_CMD, OX_FEEDLINE_PURGE_CMD]

# monitoring channels - software reads but doesn't control
MONITORING_CHANNELS = [OX_MPV_ACK, FUEL_MPV_ACK, IGNITER_ACK]

# handoff channels for avionics communication
HANDOFF_ACKS = [AVIONICS_HANDOFF_ACK, AVIONICS_STATUS_CMD] 
HANDOFF_CMDS = [AVIONICS_HANDOFF_CMD]

# List of channels we're going to read from and write to
WRITE_TO = []
READ_FROM = []
for cmd_chan in CMDS:
    WRITE_TO.append(cmd_chan)
for ack_chan in ACKS:
    READ_FROM.append(ack_chan)
for PT_chan in PTS:
    READ_FROM.append(PT_chan)
for handoff_cmd in HANDOFF_CMDS:
    WRITE_TO.append(handoff_cmd)
for handoff_ack in HANDOFF_ACKS:
    READ_FROM.append(handoff_ack)
for monitor_chan in MONITORING_CHANNELS:
    READ_FROM.append(monitor_chan)
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

# TODO: Update these values based on testing requirements
MPV_DELAY = 0.281  # seconds
# OX_MPV takes 0.357 s to reach chamber
# FUEL_MPV used to take 0.246 s to reach chamber
# FUEL_MPV now takes 0.276 s to reach chamber
# This delay puts OX in the chamber 0.200 seconds before fuel

# handoff timing parameters
HANDOFF_TIMEOUT = 5.0  # seconds
IGNITION_DELAY = 6.0   # seconds
ISO_DELAY = 2  # seconds

# handoff status tracking
HANDOFF_SUCCESSFUL = False
HANDOFF_ATTEMPTED = False

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


with client.control.acquire("Pre Press + Reg Fire", READ_FROM, WRITE_TO, 200) as auto:
    # creates valve objects for each valve (except MPV/igniter - controlled by avionics)
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

    def avionics_handoff(auto: Controller) -> bool:
        # handoff MPV control to avionics, returns True if successful
        global HANDOFF_SUCCESSFUL, HANDOFF_ATTEMPTED
        
        print("\n" + "="*60)
        print("CRITICAL: INITIATING HANDOFF TO AVIONICS")
        print("="*60)
        
        HANDOFF_ATTEMPTED = True
        handoff_start_time = time.time()
        
        try:
            # Step 1: Send handoff command to avionics
            print("Step 1: Sending handoff command to avionics...")
            auto[AVIONICS_HANDOFF_CMD] = 1  # Signal avionics to take control
            print(f"Handoff command sent at {time.time():.3f}")
            
            # Step 2: Wait for avionics acknowledgment with timeout
            print(f"Step 2: Waiting for avionics acknowledgment (timeout: {HANDOFF_TIMEOUT}s)...")
            ack_received = False
            
            while (time.time() - handoff_start_time) < HANDOFF_TIMEOUT:
                if auto[AVIONICS_HANDOFF_ACK] == 1:
                    ack_received = True
                    handoff_duration = time.time() - handoff_start_time
                    print(f"✓ HANDOFF ACKNOWLEDGED in {handoff_duration:.3f}s")
                    break
                time.sleep(0.1)  # Check every 100ms
            
            if not ack_received:
                print("✗ HANDOFF TIMEOUT - Avionics did not acknowledge")
                print("ABORTING - Maintaining software control")
                auto[AVIONICS_HANDOFF_CMD] = 0  # Cancel handoff
                return False
            
            # Step 3: Verify avionics is ready
            print("Step 3: Verifying avionics readiness...")
            if auto[AVIONICS_STATUS_CMD] == 1:  # Avionics reports ready
                print("✓ AVIONICS READY - Handoff complete")
                HANDOFF_SUCCESSFUL = True
                print("SOFTWARE PHASE COMPLETE - AVIONICS NOW IN CONTROL")
                print("="*60)
                return True
            else:
                print("✗ AVIONICS NOT READY - Handoff failed")
                auto[AVIONICS_HANDOFF_CMD] = 0  # Cancel handoff
                return False
                
        except Exception as e:
            print(f"✗ HANDOFF ERROR: {str(e)}")
            print("EMERGENCY: Attempting to cancel handoff...")
            try:
                auto[AVIONICS_HANDOFF_CMD] = 0
            except:
                print("CRITICAL: Cannot cancel handoff - manual intervention required")
            return False
    
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
        input("Press any key to continue or ctrl-c to fully abort")
            
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

    def reg_fire():
        # launch sequence with handoff to avionics for MPV control
        global HANDOFF_SUCCESSFUL
        
        try: 
            print("\n" + "="*50)
            print("MASA LAUNCH SEQUENCE INITIATED")
            print("="*50)
            
            print("COUNTDOWN INITIATED - T-10 seconds")
            time.sleep(1)
            print("T-9: Final system checks")
            time.sleep(1)
            print("T-8: Pressurization systems nominal")
            time.sleep(1)
            print("T-7: Ground support ready")
            time.sleep(1)
            print("T-6: Preparing for avionics handoff")
            time.sleep(1)
            print("T-5: Opening Ox Dome Iso and Ox Press Iso")
            syauto.open_all(auto, [ox_dome_iso, ox_press_iso])
            time.sleep(1)
            print("T-4: Opening Fuel Press Iso")
            syauto.open_all(auto, [fuel_press_iso])
            time.sleep(1)
            print("T-3: Ground systems ready for handoff")
            time.sleep(1)
            print("T-2: INITIATING AVIONICS HANDOFF")
            
            # CRITICAL HANDOFF POINT
            handoff_success = avionics_handoff(auto)
            
            if not handoff_success:
                print("✗ HANDOFF FAILED - ABORTING LAUNCH")
                print("Executing emergency abort sequence...")
                emergency_abort()
                return False
            
            print("T-1: AVIONICS IN CONTROL")
            time.sleep(1)
            print("T-0: LAUNCH COMMITTED - AVIONICS CONTROLLING MPVs")
            
            # From this point, avionics controls MPVs and igniter
            print(f"\nAVIONICS PHASE: Flight duration {FIRE_DURATION} seconds")
            print("Software monitoring flight progress...")
            
            # Monitor flight progress while connection exists
            connection_lost = False
            for i in range(FIRE_DURATION):
                remaining = FIRE_DURATION - i
                try:
                    # Monitor MPV status if connection still exists
                    fuel_mpv_status = auto[FUEL_MPV_ACK] if not connection_lost else "UNKNOWN"
                    ox_mpv_status = auto[OX_MPV_ACK] if not connection_lost else "UNKNOWN"
                    print(f"T+{i}s: Flight progress - FUEL MPV: {fuel_mpv_status}, OX MPV: {ox_mpv_status}")
                except:
                    if not connection_lost:
                        print(f"T+{i}s: Connection lost to rocket (expected)")
                        connection_lost = True
                    else:
                        print(f"T+{i}s: Rocket in flight (no connection)")
                time.sleep(1)

            print("\nEXPECTED FLIGHT DURATION COMPLETE")
            
            # Post-flight ground system safing (if we can still communicate)
            if not connection_lost:
                print("Connection maintained - executing post-flight safing...")
                post_flight_safing()
            else:
                print("Connection lost - executing ground system safing only...")
                ground_system_safing()
                
            print("\n" + "="*50)
            print("LAUNCH SEQUENCE COMPLETE")
            print("="*50)
            
        except KeyboardInterrupt:
            print("\n✗ LAUNCH SEQUENCE ABORTED BY OPERATOR")
            emergency_abort()
            
        except Exception as e:
            print(f"\n✗ LAUNCH SEQUENCE ERROR: {str(e)}")
            emergency_abort()
            
        return HANDOFF_SUCCESSFUL
    
    def emergency_abort():
        # emergency abort - safes all systems immediately
        print("\n" + "!"*50)
        print("EMERGENCY ABORT - SAFING ALL SYSTEMS")
        print("!"*50)
        
        try:
            # Cancel any pending handoff
            auto[AVIONICS_HANDOFF_CMD] = 0
            
            # Safe all ground systems immediately
            print("Closing all press isolation valves...")
            syauto.close_all(auto, [fuel_press_iso, ox_press_iso, ox_dome_iso])
            
            print("Opening all vents...")
            syauto.open_all(auto, [fuel_vent, ox_low_flow_vent, press_vent])
            
            print("Closing prevalves...")
            syauto.close_all(auto, [fuel_prevalve, ox_prevalve])
            
            print("Opening purge valves...")
            syauto.open_all(auto, [fuel_feedline_purge, ox_feedline_purge])
            
            print("EMERGENCY ABORT COMPLETE - ALL SYSTEMS SAFED")
            
        except Exception as e:
            print(f"CRITICAL ERROR DURING ABORT: {str(e)}")
            print("MANUAL INTERVENTION REQUIRED")
    
    def post_flight_safing():
        # post-flight safing when connection maintained
        print("Post-flight safing sequence...")
        print("Opening vents and closing ISOs")
        syauto.open_close_many_valves(auto, [fuel_vent, ox_low_flow_vent, press_vent], [fuel_press_iso, ox_press_iso])
        
        print("Opening feedline purge valves")
        syauto.open_all(auto, [fuel_feedline_purge, ox_feedline_purge])
        
        print("Closing prevalves")
        syauto.close_all(auto, [fuel_prevalve, ox_prevalve])
        
        time.sleep(5)
        print("Closing dome ISO")
        syauto.close_all(auto, [ox_dome_iso])
        
        print("Post-flight safing complete")
    
    def ground_system_safing():
        # ground system safing when rocket connection lost
        print("Ground system safing sequence...")
        print("Opening ground vents and closing ground ISOs")
        syauto.open_close_many_valves(auto, [fuel_vent, ox_low_flow_vent, press_vent], [fuel_press_iso, ox_press_iso])
        
        print("Closing prevalves")
        syauto.close_all(auto, [fuel_prevalve, ox_prevalve])
        
        time.sleep(5)
        print("Closing dome ISO")
        syauto.close_all(auto, [ox_dome_iso])
        
        print("Ground system safing complete")

    # this block runs the overall sequence
    try:
        start = datetime.now()

        input("Press enter to confirm you have opened prevalves ")

        ans = input("Type 'start' to commence autosequence. ")
        if not (ans == 'start' or ans == 'Start' or ans == 'START'):
            exit()

        print("Setting starting state")
        syauto.close_all(auto, [ox_press_iso, ox_dome_iso, fuel_vent, ox_low_flow_vent, press_vent, ox_prepress, fuel_prepress, fuel_press_iso])

        print("Pressurizing fuel and ox in 6 seconds")
        time.sleep(1)
        for i in range(5):
            print(f"{5 - i}")
            time.sleep(1)

        print("Pressurizing fuel and ox")
        auto.wait_until(pressurize)
        # the above statement will only finish if an abort is triggered

    except KeyboardInterrupt as e:
        syauto.close_all(auto, [fuel_press_iso, ox_press_iso, ox_dome_iso, fuel_prepress, ox_prepress])
        answer = input("\nValves are closed. Input `fire` to commence firing sequence anything else to skip:\n")
        if answer == "fire" or answer == "Fire" or answer == "FIRE":
            launch_success = reg_fire()

        ans = input("Firing sequence skipped - would you like to open vents and close prevalves? y/n ")
        if ans == "y":
            syauto.open_close_many_valves(auto, [fuel_vent, ox_low_flow_vent, press_vent], [fuel_prevalve, ox_prevalve])

        # # this creates a range in synnax so we can view the data
        # if real_test:
        #     rng = client.ranges.create(
        #         name=f"{start.__str__()[11:16]} Pre Press + Hotfire",
        #         time_range=sy.TimeRange(start, datetime.now() + timedelta.min(2)),
        #     )
        #     print(f"Created range for test: {rng.name}")
