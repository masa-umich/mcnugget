import time
import synnax as sy
from synnax.control.controller import Controller
import syauto

# this connects to the synnax server
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
TC1 = "gse_tc_1"
TC2 = "gse_tc_2"
TC3 = "gse_tc_3"
TC4 = "gse_tc_4"
TC5 = "gse_tc_5"
TC6 = "gse_tc_6"
TC7 = "gse_tc_7"
TC8 = "gse_tc_8"
TC9 = "gse_tc_9"
TC10 = "gse_tc_10"
TC11 = "gse_tc_11"
TC12 = "gse_tc_12"
TC13 = "gse_tc_13"
TC14 = "gse_tc_14"
TC15 = "gse_tc_15"
TC16 = "gse_tc_16"

# List of channels we're going to read from and write to
#CHANGE THESE TO LOOPS
WRITE_TO = []
READ_FROM = []
for i in range(1, 25):
    WRITE_TO.append(f"gse_doc_{i}")
    READ_FROM.append(f"gse_doa_{i}")
for i in range(1, 37):
    READ_FROM.append(f"gse_ai_{i}")
for i in range(1, 17):
    READ_FROM.append(f"gse_tc_{i}")

# Time, pressure, and other parameters to defind during testing
start = sy.TimeStamp.now()
TEST_DURATION = 30  # seconds to run the test

MAX_FUEL_TANK_PRESSURE = 700  # psi
MAX_TRAILER_PRESSURE = 150  # psi
MAX_PRESS_TANK_PRESSURE_1 = 2000 #psi
MAX_PRESS_TANK_PRESSURE_2 = 4500  # psi
MAX_OX_TANK_PRESSURE = 700  # psi
MAX_PRESS_TANK_TEMP = 140  # celsius

MIN_FUEL_TANK_PRESSURE = 450  # psi
MIN_TRAILER_PRESSURE = 50  # psi
MIN_PRESS_TANK_PRESSURE = 3900  # psi
MIN_OX_TANK_PRESSURE = 450  # psi

# PRESS_INC = 30.0  # psi

PRESS_TARGET_1 = 1800
PRESS_TARGET_2 = 4000

PRESS_INC_1 = 100
PRESS_INC_2 = 100

# specifies pressure/temp channels
FUEL_PT_1_PRESSURE = A3
FUEL_PT_2_PRESSURE = A4
FUEL_PT_3_PRESSURE = A35
TRAILER_PNEUMATICS_PRESSURE = A31
PRESS_TANK_PT_1 = A22
PRESS_TANK_PT_2 = A24
PRESS_TANK_PT_3 = A26
OX_TANK_1_PRESSURE = A6
OX_TANK_2_PRESSURE = A7
OX_TANK_3_PRESSURE = A8
PRESS_TANK_TC_1 = TC8
PRESS_TANK_TC_2 = TC9
PRESS_TANK_TC_3 = TC10
PRESS_TANK_TC_4 = TC11

print("Starting autosequence")
with client.control.acquire(name="Press and Fill Autos", write=WRITE_TO, read=READ_FROM) as auto:

    # valves for fuel system
    # fuel vent is normally open
    fuel_vent = syauto.Valve(auto=auto, cmd=v15_out,
                             ack=v15_in, normally_open=True)
    fuel_prevalve = syauto.Valve(
        auto=auto, cmd=v22_out, ack=v22_in, normally_open=False)
    # fuel_mpv = syauto.Valve(auto=auto, cmd=v3_out,
    #                         ack=v3_in, normally_open=False)

    # valves for purge system
    fuel_feedline_purge = syauto.Valve(
        auto=auto, cmd=v4_out, ack=v7_in, normally_open=False)
    ox_fill_purge = syauto.Valve(
        auto=auto, cmd=v5_out, ack=v11_in, normally_open=False)
    fuel_pre_press = syauto.Valve(
        auto=auto, cmd=v6_out, ack=v9_in, normally_open=False)
    ox_pre_press = syauto.Valve(
        auto=auto, cmd=v7_out, ack=v10_in, normally_open=False)
    ox_feedline_purge = syauto.Valve(
        auto=auto, cmd=v8_out, ack=v8_in, normally_open=False)

    # pneumatics valves
    engine_pneumatics_iso = syauto.Valve(
        auto=auto, cmd=v12_out, ack=v12_in, normally_open=False)
    # engine pneumatics vent is normally closed
    engine_pneumatics_vent = syauto.Valve(
        auto=auto, cmd=v13_out, ack=v13_in, normally_open=False)

    # press system valves
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
    fuel_press_ISO = syauto.Valve(
        auto=auto, cmd=v2_out, ack=v2_in,  normally_open=False)
    ox_press = syauto.Valve(auto=auto, cmd=v1_out,
                            ack=v1_in, normally_open=False)

    # ox press system valves
    # ox low vent is normally open
    ox_low_vent = syauto.Valve(
        auto=auto, cmd=v16_out, ack=v16_in, normally_open=True)
    ox_fill_valve = syauto.Valve(
        auto=auto, cmd=v19_out, ack=v19_in, normally_open=False)
    # ox high flow vent is normally open
    ox_high_flow_vent = syauto.Valve(
        auto=auto, cmd=v17_out, ack=v17_in, normally_open=False)
    # ox_MPV = syauto.Valve(auto=auto, cmd=v22_out,
    #                       ack=v22_in, normally_open=False)
    ox_pre_valve = syauto.Valve(auto=auto, cmd=v21_out,
                                ack=v21_in, normally_open=False)

    pre_valves = [fuel_prevalve, ox_pre_valve]
    press_valves = [fuel_press_ISO, ox_press, air_drive_ISO_1,
                    air_drive_ISO_2, engine_pneumatics_iso]

    all_vents = [fuel_vent, engine_pneumatics_vent,
                 press_vent, ox_low_vent]

    all_valves = [fuel_prevalve, fuel_feedline_purge, ox_fill_purge, fuel_pre_press,
                  ox_pre_press, ox_feedline_purge, engine_pneumatics_iso,
                  air_drive_ISO_1, air_drive_ISO_2, gas_booster_fill, press_fill, fuel_press_ISO,
                  ox_press, ox_fill_valve]

    #Returns TRUE if an abort is needed, otherwise returns FALSE
    def abort_during_press_tank_fill(auto_: Controller):
        press_tank_1_press = auto_[PRESS_TANK_PT_1]
        press_tank_2_press = auto_[PRESS_TANK_PT_2]
        press_tank_3_press = auto_[PRESS_TANK_PT_3]
        # If any press tank exceeds max pressure, returns TRUE
        if (press_tank_1_press> MAX_PRESS_TANK_PRESSURE_2
            or press_tank_2_press > MAX_PRESS_TANK_PRESSURE_2
            or press_tank_3_press > MAX_PRESS_TANK_PRESSURE_2):
            print("At least one press tank has exceeded maximum pressure - ABORTING")
            syauto.close_all(auto_, {air_drive_ISO_1, air_drive_ISO_2, press_fill, gas_booster_fill})
            print("Abort complete: air drive isos, gas booster, and press fill closed")
            return True
        
        # If any press tank temperature is above the accepted maximum, returns TRUE
        if (auto_[PRESS_TANK_TC_1] > MAX_PRESS_TANK_TEMP
            or auto_[PRESS_TANK_TC_2] > MAX_PRESS_TANK_TEMP
            or auto_[PRESS_TANK_TC_3] > MAX_PRESS_TANK_TEMP
                or auto_[PRESS_TANK_TC_4] > MAX_PRESS_TANK_TEMP):
            print("temperature has exceeded acceptable range - ABORTING")
            syauto.close_all(auto_, {air_drive_ISO_1, air_drive_ISO_2, press_fill, gas_booster_fill})
            print("Abort complete: air drive isos, gas booster, and press fill closed")
            return True

        return False

    try:
        """
        this code does the following:
            - sets an initial state with VALVES and VENTS both closed
            - equalizes pressure between 2K bottles and PRESS_TANKS     {PRESS_TARGET_1}
            - uses gas booster to pressurize PRESS_TANKS                {PRESS_TARGET_2}
        """

        # starting opening all valves and closing all vents
        print("Starting Press Fill Autosequence. Setting initial system state.")
        syauto.close_all(auto, all_valves+all_vents)
        time.sleep(1)

        print("PHASE 1: 2K Bottle Equalization")
        print(
            f"pressurizing PRESS_TANKS 1-3 to {PRESS_TARGET_1} using {press_fill} in increments of {PRESS_INC_1} ")
        syauto.pressurize(auto, press_fill, 
                        [PRESS_TANK_PT_1, PRESS_TANK_PT_2, PRESS_TANK_PT_3],
                        PRESS_TARGET_1, MAX_PRESS_TANK_PRESSURE_1, PRESS_INC_1)
        print("Pressurization phase 1 complete")
        press_fill.close()
        input("Press any key to continue")

        print("PHASE 2: Pressurization with Gas Booster")
        gas_booster_fill.open()
        print(
            f"pressurizing PRESS_TANKS 1-3 to {PRESS_TARGET_2} using {air_drive_ISO_1} and {air_drive_ISO_2} in increments of {PRESS_INC_2}")
        syauto.pressurize(auto,[air_drive_ISO_1, air_drive_ISO_2], [
                          PRESS_TANK_PT_1, PRESS_TANK_PT_2, PRESS_TANK_PT_3], PRESS_TARGET_2 - PRESS_TARGET_1, MAX_PRESS_TANK_PRESSURE_2, PRESS_INC_2)
        gas_booster_fill.close()

        print("Test complete. Safing System")
        syauto.open_close_many_valves(auto, all_vents, all_valves)
        print("Valves closed and vents open")

        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} shakedown Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

    except KeyboardInterrupt as e:
        # Handle Ctrl+C interruption
        if str(e) == "Interrupted by user.":
            print("Test interrupted. Safeing System")
            syauto.open_close_many_valves(auto, all_vents, all_valves)

    time.sleep(60)
