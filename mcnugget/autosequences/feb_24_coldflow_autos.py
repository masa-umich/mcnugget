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

#Connects to masa cluster
# client = sy.Synnax(
#     host="MASA Remote",
#     port=80,
#     username="synnax.masa.engin.umich.edu",
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
v25_in = "gse_doa_25"
v25_out = "gse_doc_25"

# sensor names to channel names
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

# List of channels we're going to read from and write to
WRITE_TO = [v1_out, v2_out, v3_out, v4_out, v5_out, v6_out, v7_out, v8_out, v9_out, v10_out,
            v11_out, v12_out, v13_out, v14_out, v15_out, v16_out, v17_out, v18_out, v19_out, v20_out,
            v21_out, v22_out, v23_out, v24_out, v25_out]

READ_FROM = [v1_in, v2_in, v3_in, v4_in, v5_in, v6_in, v7_in, v8_in, v9_in, v10_in,
             v11_in, v12_in, v13_in, v14_in, v15_in, v16_in, v17_in, v18_in, v19_in, v20_in, v21_in,
             v22_in, v23_in, v24_in, v25_in,
             A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18, A19, A20]

# Time, pressure, and other parameters to defind during testing
start = sy.TimeStamp.now()
TEST_DURATION = 30  # seconds to run the test
MAX_FUEL_TANK_PRESSURE = 700  # psi
MAX_TRAILER_PRESSURE = 150  # psi
MAX_PRESS_TANK_PRESSURE = 4500  # psi
MAX_OX_TANK_PRESSURE = 700  # psi

MIN_FUEL_TANK_PRESSURE = 450  # psi
MIN_TRAILER_PRESSURE = 50  # psi
MIN_PRESS_TANK_PRESSURE = 3900  # psi
MIN_OX_TANK_PRESSURE = 450  # psi


print("Starting autosequence")
with client.control.acquire(name="shakedown", write=WRITE_TO, read=READ_FROM) as auto:

    # valves for fuel system
    # fuel vent is normally open
    fuel_vent = syauto.Valve(auto=auto, cmd=v1_out,
                             ack=v1_in, normally_open=True)
    fuel_prevalve = syauto.Valve(
        auto=auto, cmd=v2_out, ack=v2_in, normally_open=False)
    fuel_mpv = syauto.Valve(auto=auto, cmd=v3_out,
                            ack=v3_in, normally_open=False)

    # valves for purge system
    fuel_feedline_purge = syauto.Valve(
        auto=auto, cmd=v4_out, ack=v4_in, normally_open=False)
    ox_fill_purge = syauto.Valve(
        auto=auto, cmd=v5_out, ack=v5_in, normally_open=False)
    fuel_pre_press = syauto.Valve(
        auto=auto, cmd=v6_out, ack=v6_in, normally_open=False)
    ox_pre_press = syauto.Valve(
        auto=auto, cmd=v7_out, ack=v7_in, normally_open=False)
    ox_feedline_purge = syauto.Valve(
        auto=auto, cmd=v8_out, ack=v8_in, normally_open=False)

    # pneumatics valves
    engine_pneumatics_iso = syauto.Valve(
        auto=auto, cmd=v9_out, ack=v9_in, normally_open=False)
    # engine pneumatics vent is normally open
    engine_pneumatics_vent = syauto.Valve(
        auto=auto, cmd=v10_out, ack=v10_in, normally_open=False)
    solenoid_manifold = syauto.Valve(
        auto=auto, cmd=v11_out, ack=v11_in, normally_open=False)

    # press system valves
    air_drive_ISO_1 = syauto.Valve(
        auto=auto, cmd=v12_out, ack=v12_in, normally_open=False)
    air_drive_ISO_2 = syauto.Valve(
        auto=auto, cmd=v13_out, ack=v13_in, normally_open=False)
    gas_booster_fill = syauto.Valve(
        auto=auto, cmd=v14_out, ack=v14_in, normally_open=False)
    press_fill = syauto.Valve(auto=auto, cmd=v15_out,
                              ack=v15_in, normally_open=False)
    # press vent is normally open
    press_vent = syauto.Valve(auto=auto, cmd=v16_out,
                              ack=v16_in, normally_open=True)
    fuel_press_ISO = syauto.Valve(
        auto=auto, cmd=v17_out, ack=v17_in,  normally_open=False)
    ox_press = syauto.Valve(auto=auto, cmd=v18_out,
                            ack=v18_in, normally_open=False)

    # ox press system valves
    # ox low vent is normally open
    ox_low_vent = syauto.Valve(
        auto=auto, cmd=v19_out, ack=v19_in, normally_open=True)
    ox_fill_valve = syauto.Valve(
        auto=auto, cmd=v20_out, ack=v20_in, normally_open=False)
    # ox high flow vent is normally open
    ox_high_flow_vent = syauto.Valve(
        auto=auto, cmd=v21_out, ack=v21_in, normally_open=False)
    ox_MPV = syauto.Valve(auto=auto, cmd=v22_out,
                          ack=v22_in, normally_open=False)
    ox_pre_valve = syauto.Valve(auto=auto, cmd=v23_out,
                                ack=v23_in, normally_open=False)

    pre_valves = [fuel_prevalve, ox_pre_valve]
    press_valves = [fuel_press_ISO, ox_press, air_drive_ISO_1, air_drive_ISO_2, engine_pneumatics_iso]

    all_vents = [fuel_vent, engine_pneumatics_vent,
                 press_vent, ox_low_vent]

    all_valves = [fuel_prevalve, fuel_mpv, fuel_feedline_purge, ox_fill_purge, fuel_pre_press,
                  ox_pre_press, ox_feedline_purge, engine_pneumatics_iso, solenoid_manifold,
                  air_drive_ISO_1, air_drive_ISO_2, gas_booster_fill, press_fill, fuel_press_ISO,
                  ox_press, ox_fill_valve, ox_MPV]

    def run_shakedown(auto_: Controller):
        fuel_pt_1_pressure = auto_[A1]
        fuel_pt_2_pressure = auto_[A2]
        fuel_pt_3_pressure = auto_[A3]
        trailer_pnematics_pressure = auto_[A4]
        press_tank_pt_1 = auto_[A5]
        press_tank_pt_2 = auto_[A6]
        press_tank_pt_3 = auto_[A7]
        ox_tank_1_pressure = auto_[A8]
        ox_tank_2_pressure = auto_[A9]
        ox_tank_3_pressure = auto_[A10]

        # aborts if the pressure is above the accepted maximum
        if (fuel_pt_1_pressure > MAX_FUEL_TANK_PRESSURE or fuel_pt_2_pressure > MAX_FUEL_TANK_PRESSURE or fuel_pt_3_pressure > MAX_FUEL_TANK_PRESSURE or
                trailer_pnematics_pressure > MAX_TRAILER_PRESSURE or press_tank_pt_1 > MAX_PRESS_TANK_PRESSURE or
                press_tank_pt_2 > MAX_PRESS_TANK_PRESSURE or press_tank_pt_3 > MAX_PRESS_TANK_PRESSURE
                or ox_tank_1_pressure > MAX_FUEL_TANK_PRESSURE or ox_tank_2_pressure > MAX_FUEL_TANK_PRESSURE or
                ox_tank_3_pressure > MAX_FUEL_TANK_PRESSURE):
            print("pressure has exceeded acceptable range - ABORTING and opening all vents")
            syauto.open_close_many_valves(auto, all_valves, all_vents)
            print(f"All vents open, closing pre-valves")

        # aborts if the pressure is below the accepted minimum (-20 below target)
        if (fuel_pt_1_pressure < MIN_FUEL_TANK_PRESSURE or fuel_pt_2_pressure < MIN_FUEL_TANK_PRESSURE or fuel_pt_3_pressure < MIN_FUEL_TANK_PRESSURE or
                trailer_pnematics_pressure < MIN_TRAILER_PRESSURE or press_tank_pt_1 < MIN_PRESS_TANK_PRESSURE or press_tank_pt_2 < MIN_PRESS_TANK_PRESSURE or
                press_tank_pt_3 < MIN_PRESS_TANK_PRESSURE or ox_tank_1_pressure < MIN_OX_TANK_PRESSURE or ox_tank_2_pressure < MIN_OX_TANK_PRESSURE or
                ox_tank_3_pressure < MIN_OX_TANK_PRESSURE):
            print(f"pressure below 15 - ABORTING and opening all vents")
            syauto.open_close_many_valves(auto, all_valves, all_vents)
            print(f"All vents open, closing pre-valves")

        # if the pressure drops below 15, the tanks are mostly empty and the test is finished
        return (fuel_pt_1_pressure < 15 or fuel_pt_2_pressure < 15 or fuel_pt_3_pressure < 15 or
                trailer_pnematics_pressure < 15 or press_tank_pt_1 < 15 or press_tank_pt_2 < 15 or
                press_tank_pt_3 < 15 or ox_tank_1_pressure < 15 or ox_tank_2_pressure < 15 or
                ox_tank_3_pressure < 15)

    try:
        # starting opening all valves and closing all vents
        print("Starting Shakedown Test. Setting initial system state.")
        syauto.open_close_many_valves(auto, pre_valves+press_valves, all_vents)
        # syauto.close_all(auto, all_vents)
        #time.sleep(1)
        # syauto.open_all(auto, pre_valves+press_valves)
        time.sleep(2)

        # print("Purging system for " + str(TEST_DURATION) + " seconds")
        # syauto.purge(all_valves, TEST_DURATION)
        auto.wait_until(run_shakedown, timeout=TEST_DURATION)
        time.sleep(1)
        
        print("Test complete. Safing System")
        syauto.open_close_many_valves(auto, all_vents, pre_valves+press_valves)
        print("Valves closed and vents open")

        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} shakedown Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

    except KeyboardInterrupt as e:
        # Handle Ctrl+C interruption
        if str(e) == "Interrupted by user.":
            print("Test interrupted. Safeing System")
            syauto.open_close_many_valves(auto, all_valves, all_vents)

        # Handle 'x' key interruption
        elif str(e) == "Interrupted by user. (x)":
            print("Test interrupted. Safeing System")
            syauto.open_close_many_valves(auto, all_valves, all_vents)

    time.sleep(60)
