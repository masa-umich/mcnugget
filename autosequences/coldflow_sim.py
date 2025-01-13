import time
import random
import synnax as sy

client = sy.Synnax(
    host="localhost", port=9090, username="synnax", password="seldon", secure=False
)

# testing if leon can git push
DAQ_TIME = "daq_time"

# valves for fuel system
FUEL_VENT_IN = "gse_state_15"
FUEL_VENT_OUT = "gse_doc_15"
FUEL_PREVALVE_IN = "gse_state_22"
FUEL_PREVALVE_OUT = "gse_doc_22"
FUEL_MPV_IN = "gse_state_24"
FUEL_MPV_OUT = "gse_doc_24"

# valves for purge system
FUEL_FEEDLINE_PURGE_IN = "gse_state_7"
FUEL_FEEDLINE_PURGE_OUT = "gse_doc_7"
OX_FILL_PURGE_IN = "gse_state_11"
OX_FILL_PURGE_OUT = "gse_doc_11"
OX_FEEDLINE_PURGE_IN = "gse_state_8"
OX_FEEDLINE_PURGE_OUT = "gse_doc_8"

# valves for pneumatics
ENGINE_PNEUMATICS_ISO_IN = "gse_state_12"
ENGINE_PNEUMATICS_ISO_OUT = "gse_doc_12"
ENGINE_PNEUMATICS_VENT_IN = "gse_state_13"
ENGINE_PNEUMATICS_VENT_OUT = "gse_doc_13"

# valves for press system
AIR_DRIVE_ISO_1_IN = "gse_state_5"
AIR_DRIVE_ISO_1_OUT = "gse_doc_5"
AIR_DRIVE_ISO_2_IN = "gse_state_4"
AIR_DRIVE_ISO_2_OUT = "gse_doc_4"
GAS_BOOSTER_FILL_IN = "gse_state_20"
GAS_BOOSTER_FILL_OUT = "gse_doc_20"
PRESS_FILL_IN = "gse_state_23"
PRESS_FILL_OUT = "gse_doc_23"
PRESS_VENT_IN = "gse_state_18"
PRESS_VENT_OUT = "gse_doc_18"
FUEL_PRESS_ISO_IN = "gse_state_2"
FUEL_PRESS_ISO_OUT = "gse_doc_2"
OX_PRESS_IN = "gse_state_1"
OX_PRESS_OUT = "gse_doc_1"
PRE_PRESS_IN = "gse_state_10"
PRE_PRESS_OUT = "gse_doc_10"

# Ox system pressure valves
OX_LOW_VENT_IN = "gse_state_16"
OX_LOW_VENT_OUT = "gse_doc_16"
OX_FILL_VALVE_IN = "gse_state_19"
OX_FILL_VALVE_OUT = "gse_doc_19"
OX_HIGH_FLOW_VENT_IN = "gse_state_17"
OX_HIGH_FLOW_VENT_OUT = "gse_doc_17"
OX_PREVALVE_IN = "gse_state_21"
OX_PRE_VALVE_OUT = "gse_doc_21"
OX_DOME_ISO_IN = "gse_state_3"
OX_DOME_ISO_OUT = "gse_doc_3"
OX_DRAIN_IN = "gse_state_14"
OX_DRAIN_OUT = "gse_doc_14"
OX_MPV_IN = "gse_state_6"
OX_MPV_OUT = "gse_doc_6"

IGNITOR_IN = "gse_state_25"
IGNITOR_OUT = "gse_doc_25"

command_channels = [
    FUEL_VENT_OUT,
    FUEL_PREVALVE_OUT,
    FUEL_FEEDLINE_PURGE_OUT,
    OX_FILL_PURGE_OUT,
    OX_FEEDLINE_PURGE_OUT,
    ENGINE_PNEUMATICS_ISO_OUT,
    ENGINE_PNEUMATICS_VENT_OUT,
    AIR_DRIVE_ISO_1_OUT,
    AIR_DRIVE_ISO_2_OUT,
    GAS_BOOSTER_FILL_OUT,
    PRESS_FILL_OUT,
    PRESS_VENT_OUT,
    FUEL_PRESS_ISO_OUT,
    OX_PRESS_OUT,
    OX_LOW_VENT_OUT,
    OX_FILL_VALVE_OUT,
    OX_HIGH_FLOW_VENT_OUT,
    OX_PRE_VALVE_OUT,
    OX_DOME_ISO_OUT,
    OX_MPV_OUT,
    FUEL_MPV_OUT,
    IGNITOR_OUT,
    PRE_PRESS_OUT,
]

ack_channels = [
    FUEL_VENT_IN,
    FUEL_PREVALVE_IN,
    FUEL_FEEDLINE_PURGE_IN,
    OX_FILL_PURGE_IN,
    OX_FEEDLINE_PURGE_IN,
    ENGINE_PNEUMATICS_ISO_IN,
    ENGINE_PNEUMATICS_VENT_IN,
    AIR_DRIVE_ISO_1_IN,
    AIR_DRIVE_ISO_2_IN,
    GAS_BOOSTER_FILL_IN,
    PRESS_FILL_IN,
    PRESS_VENT_IN,
    FUEL_PRESS_ISO_IN,
    OX_PRESS_IN,
    OX_LOW_VENT_IN,
    OX_FILL_VALVE_IN,
    OX_HIGH_FLOW_VENT_IN,
    OX_PREVALVE_IN,
    OX_DOME_ISO_IN,
    OX_MPV_IN,
    FUEL_MPV_IN,
    IGNITOR_IN,
    PRE_PRESS_IN,
]

# Pressure sensors
OX_PRE_FILL_PT = "gse_ai_1"
OX_PRESS_DOME_PILOT_REG_PT = "gse_ai_2"
FUEL_PT_1_PRESSURE = "gse_ai_3"
FUEL_PT_2_PRESSURE = "gse_ai_4"
OX_PRESS_PT = "gse_ai_5"
OX_TANK_1_PRESSURE = "gse_ai_6"
OX_TANK_2_PRESSURE = "gse_ai_7"
OX_TANK_3_PRESSURE = "gse_ai_8"
OX_FLOWMETER_INLET_PT = "gse_ai_9"
OX_FLOWMETER_THROAT_PT = "gse_ai_10"
OX_LEVEL_SENSOR = "gse_ai_11"
FUEL_FLOWMETER_INLET_PT = "gse_ai_12"
FUEL_FLOWMETER_THROAT_PT = "gse_ai_13"
FUEL_LEVEL_SENSOR = "gse_ai_14"
TRICKLE_PURGE_POST_REG_PT = "gse_ai_15"
TRICKLE_PURGE_PRE_2K_PT = "gse_ai_16"
AIR_DRIVE_2K_PT = "gse_ai_20"
AIR_DRIVE_POST_REG_PT = "gse_ai_21"
PRESS_TANK_SUPPLY = "gse_ai_23"
GAS_BOOSTER_OUTLET_PT = "gse_ai_25"
PRESS_TANK_2K_BOTTLE_PRE_FILL_PT = "gse_ai_27"
PNEUMATICS_BOTTLE_PT = "gse_ai_30"
TRAILER_PNEMATICS_PT = "gse_ai_31"
ENGINE_PNEUMATICS_PT = "gse_ai_33"
PURGE_2K_BOTTLE_PT = "gse_ai_34"
PURGE_POST_REG_PT = "gse_ai_36"
FUEL_PT_3_PRESSURE = "gse_ai_35"
PRESS_TANK_PT_1 = "gse_ai_26"
PRESS_TANK_PT_2 = "gse_ai_24"
PRESS_TANK_PT_3 = "gse_ai_22"

PTs = [
    OX_PRE_FILL_PT,
    OX_PRESS_DOME_PILOT_REG_PT,
    FUEL_PT_1_PRESSURE,
    FUEL_PT_2_PRESSURE,
    FUEL_PT_3_PRESSURE,
    OX_PRESS_PT,
    OX_TANK_1_PRESSURE,
    OX_TANK_2_PRESSURE,
    OX_TANK_3_PRESSURE,
    OX_FLOWMETER_INLET_PT,
    OX_FLOWMETER_THROAT_PT,
    OX_LEVEL_SENSOR,
    FUEL_FLOWMETER_INLET_PT,
    FUEL_FLOWMETER_THROAT_PT,
    FUEL_LEVEL_SENSOR,
    TRICKLE_PURGE_POST_REG_PT,
    TRICKLE_PURGE_PRE_2K_PT,
    AIR_DRIVE_2K_PT,
    AIR_DRIVE_POST_REG_PT,
    PRESS_TANK_SUPPLY,
    GAS_BOOSTER_OUTLET_PT,
    PRESS_TANK_PT_1,
    PRESS_TANK_PT_2,
    PRESS_TANK_PT_3,
    PRESS_TANK_2K_BOTTLE_PRE_FILL_PT,
    PNEUMATICS_BOTTLE_PT,
    TRAILER_PNEMATICS_PT,
    ENGINE_PNEUMATICS_PT,
    PURGE_2K_BOTTLE_PT,
    PURGE_POST_REG_PT,
]

# Parameters for testing
INITIAL_FUEL_TANK_PRESSURE = 0
INITIAL_OX_TANK_PRESSURE = 0
INITIAL_PRESS_TANK_PRESSURE = 0
INITIAL_2K_PRESSURE = 2000

daq_time = client.channels.create(
    name=DAQ_TIME,
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

for i in range(1, 30):
    idx = client.channels.create(
        name=f"gse_doc_{i}_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True,
    )
    client.channels.create(
        name=f"gse_doc_{i}",
        data_type=sy.DataType.UINT8,
        index=idx.key,
        retrieve_if_name_exists=True,
    )
    client.channels.create(
        name=f"gse_state_{i}",
        data_type=sy.DataType.UINT8,
        index=daq_time.key,
        retrieve_if_name_exists=True,
    )

for pt in PTs:
    client.channels.create(
        name=pt,
        data_type=sy.DataType.FLOAT32,
        index=daq_time.key,
        retrieve_if_name_exists=True,
    )

rate = (sy.Rate.HZ * 50).period.seconds
print("rate: ", rate)

DAQ_STATE = {}

for cmd_chan in command_channels:
    DAQ_STATE[cmd_chan] = 0

DAQ_STATE[OX_PRE_VALVE_OUT] = 0
DAQ_STATE[FUEL_PREVALVE_OUT] = 0
DAQ_STATE[OX_MPV_OUT] = 1
DAQ_STATE[FUEL_MPV_OUT] = 1

for pt in PTs:
    DAQ_STATE[pt] = 0

DAQ_STATE[IGNITOR_OUT] = 0

DAQ_STATE.update(
    {
        FUEL_PT_1_PRESSURE: INITIAL_FUEL_TANK_PRESSURE,
        FUEL_PT_2_PRESSURE: INITIAL_FUEL_TANK_PRESSURE,
        FUEL_PT_3_PRESSURE: INITIAL_FUEL_TANK_PRESSURE,
        PRESS_TANK_PT_1: INITIAL_PRESS_TANK_PRESSURE,
        PRESS_TANK_PT_2: INITIAL_PRESS_TANK_PRESSURE,
        PRESS_TANK_PT_3: INITIAL_PRESS_TANK_PRESSURE,
        OX_TANK_1_PRESSURE: 0,
        OX_TANK_2_PRESSURE: 0,
        OX_TANK_3_PRESSURE: 0,
    }
)

true_fuel_pressure = INITIAL_FUEL_TANK_PRESSURE
fuel_PT_1_pressure = true_fuel_pressure + random.uniform(-20, 20)
fuel_PT_2_pressure = true_fuel_pressure + random.uniform(-20, 20)
fuel_PT_3_pressure = true_fuel_pressure + random.uniform(-20, 20)

true_ox_pressure = INITIAL_OX_TANK_PRESSURE
ox_tank_1_pressure = true_ox_pressure + random.uniform(-20, 20)
ox_tank_2_pressure = true_ox_pressure + random.uniform(-20, 20)
ox_tank_3_pressure = true_ox_pressure + random.uniform(-20, 20)

true_press_pressure = INITIAL_PRESS_TANK_PRESSURE
press_tank_PT_1 = true_press_pressure + random.uniform(-20, 20)
press_tank_PT_2 = true_press_pressure + random.uniform(-20, 20)
press_tank_PT_3 = true_press_pressure + random.uniform(-20, 20)

supply_2k = INITIAL_2K_PRESSURE

FUEL_PREVALVE_LAST_OPEN = None
OX_PREVALVE_LAST_OPEN = None
FUEL_MPV_LAST_OPEN = None
OX_MPV_LAST_OPEN = None

READ_CHANNELS = command_channels
WRITE_CHANNELS = ack_channels + PTs + [DAQ_TIME]  # + TCs
print(f"writing to {len(WRITE_CHANNELS)} channels")
print(f"reading from {len(READ_CHANNELS)} channels")

with client.open_streamer(READ_CHANNELS) as streamer:
    with client.open_writer(
        sy.TimeStamp.now(),
        channels=WRITE_CHANNELS,
        name="daq_sim",
        enable_auto_commit=True,
    ) as writer:
        print(len(WRITE_CHANNELS))
        for wc in WRITE_CHANNELS:
            print(wc)
        i = 0
        while True:
            try:
                time.sleep(rate)
                while True:
                    f = streamer.read(0)
                    if f is None:
                        # print("done")
                        break
                    else:
                        print("received: ", f)
                    for c in f.channels:
                        DAQ_STATE[c] = f[c][-1]
                        print(f"{c}: {f[c][-1]}")

                fuel_vent_energized = DAQ_STATE[FUEL_VENT_OUT] == 1
                fuel_prevalve_energized = DAQ_STATE[FUEL_PREVALVE_OUT] == 1
                fuel_press_iso_energized = DAQ_STATE[FUEL_PRESS_ISO_OUT] == 1
                fuel_mpv_energized = DAQ_STATE[FUEL_MPV_OUT] == 1
                ox_press_energized = DAQ_STATE[OX_PRESS_OUT] == 1
                ox_low_vent_energized = DAQ_STATE[OX_LOW_VENT_OUT] == 1
                ox_fill_valve_energized = DAQ_STATE[OX_FILL_VALVE_OUT] == 1
                ox_high_flow_vent_energized = DAQ_STATE[OX_HIGH_FLOW_VENT_OUT] == 1
                ox_pre_valve_energized = DAQ_STATE[OX_PRE_VALVE_OUT] == 1
                ox_pre_fill_energized = DAQ_STATE[OX_PRE_FILL_PT] == 1
                ox_dome_iso_energized = DAQ_STATE[OX_DOME_ISO_OUT] == 1
                ox_mpv_energized = DAQ_STATE[OX_MPV_OUT] == 1
                air_drive_iso_1_energized = DAQ_STATE[AIR_DRIVE_ISO_1_OUT] == 1
                air_drive_iso_2_energized = DAQ_STATE[AIR_DRIVE_ISO_2_OUT] == 1
                gas_booster_fill_energized = DAQ_STATE[GAS_BOOSTER_FILL_OUT] == 1
                press_fill_energized = DAQ_STATE[PRESS_FILL_OUT] == 1
                press_vent_energized = DAQ_STATE[PRESS_VENT_OUT] == 1
                ignitor_energized = DAQ_STATE[IGNITOR_OUT] == 1
                pre_press_energized = DAQ_STATE[PRE_PRESS_OUT] == 1

                fuel_tank_delta = -0.05
                trailer_pneumatics_delta = -0.005
                press_tank_delta = -1
                ox_tank_delta = -0.07

                ### PRESS ###
                if press_fill_energized:
                    if supply_2k > true_press_pressure:
                        diff = (supply_2k / INITIAL_2K_PRESSURE) * 6 + 0.1
                        press_tank_delta += diff
                        supply_2k -= diff / 8
                    if gas_booster_fill_energized:
                        if air_drive_iso_1_energized and air_drive_iso_2_energized:
                            diff = (supply_2k / INITIAL_2K_PRESSURE) * 6 + 1
                            press_tank_delta += diff
                            supply_2k -= diff / 8

                if not press_vent_energized:
                    press_tank_delta -= 4

                ### FUEL ###
                if fuel_prevalve_energized and FUEL_PREVALVE_LAST_OPEN is None:
                    FUEL_PREVALVE_LAST_OPEN = sy.TimeStamp.now()
                elif not fuel_prevalve_energized:
                    FUEL_PREVALVE_LAST_OPEN = None

                if fuel_mpv_energized and FUEL_MPV_LAST_OPEN is None:
                    FUEL_MPV_LAST_ENERGIZED = sy.TimeStamp.now()
                elif not fuel_mpv_energized:
                    FUEL_MPV_LAST_ENERGIZED = None

                if fuel_press_iso_energized:
                    press_tank_delta -= 1.5
                    fuel_tank_delta += 1.5

                if fuel_prevalve_energized and fuel_mpv_energized:
                    fuel_tank_delta -= (
                        0.5
                        * sy.TimeSpan(
                            sy.TimeStamp.now() - FUEL_MPV_LAST_ENERGIZED
                        ).seconds
                    )

                if not fuel_vent_energized:
                    fuel_tank_delta -= 3

                ### OX ###
                if ox_pre_valve_energized and OX_PREVALVE_LAST_OPEN is None:
                    OX_PREVALVE_LAST_OPEN = sy.TimeStamp.now()
                elif not ox_pre_valve_energized:
                    OX_PREVALVE_LAST_OPEN = None

                if ox_mpv_energized and OX_MPV_LAST_OPEN is None:
                    OX_MPV_LAST_ENERGIZED = sy.TimeStamp.now()
                elif not ox_mpv_energized:
                    OX_MPV_LAST_ENERGIZED = None

                if ox_press_energized:
                    press_tank_delta -= 1.5
                    ox_tank_delta += 1.5

                if ox_pre_valve_energized and ox_mpv_energized:
                    ox_tank_delta -= (
                        0.5
                        * sy.TimeSpan(
                            sy.TimeStamp.now() - OX_PREVALVE_LAST_OPEN
                        ).seconds
                    )

                if not ox_low_vent_energized:
                    ox_tank_delta -= 2.0

                if not ox_high_flow_vent_energized:
                    ox_tank_delta -= 5.0

                true_ox_pressure += ox_tank_delta
                true_fuel_pressure += fuel_tank_delta
                true_press_pressure += press_tank_delta

                # no negative pressures pls ;-;
                true_ox_pressure = max(0, true_ox_pressure)
                true_fuel_pressure = max(0, true_fuel_pressure)
                true_press_pressure = max(0, true_press_pressure)
                supply_2k = max(0, supply_2k)

                if true_press_pressure > 3800:
                    raise Exception("You just blew up a press tank")

                now = sy.TimeStamp.now()

                write_data = {
                    DAQ_TIME: now,
                    FUEL_VENT_IN: int(fuel_vent_energized),
                    FUEL_PREVALVE_IN: int(fuel_prevalve_energized),
                    FUEL_FEEDLINE_PURGE_IN: 0,
                    OX_FILL_PURGE_IN: 0,
                    OX_FEEDLINE_PURGE_IN: 0,
                    ENGINE_PNEUMATICS_ISO_IN: 0,
                    ENGINE_PNEUMATICS_VENT_IN: 0,
                    AIR_DRIVE_ISO_1_IN: int(air_drive_iso_1_energized),
                    AIR_DRIVE_ISO_2_IN: int(air_drive_iso_2_energized),
                    GAS_BOOSTER_FILL_IN: int(gas_booster_fill_energized),
                    PRESS_FILL_IN: int(press_fill_energized),
                    PRESS_VENT_IN: int(press_vent_energized),
                    FUEL_PRESS_ISO_IN: int(fuel_press_iso_energized),
                    OX_PRESS_IN: int(ox_press_energized),
                    OX_LOW_VENT_IN: int(ox_low_vent_energized),
                    OX_FILL_VALVE_IN: int(ox_fill_valve_energized),
                    OX_HIGH_FLOW_VENT_IN: int(ox_high_flow_vent_energized),
                    OX_PREVALVE_IN: int(ox_pre_valve_energized),
                    OX_DOME_ISO_IN: int(ox_dome_iso_energized),
                    FUEL_MPV_IN: int(fuel_mpv_energized),
                    OX_MPV_IN: int(ox_mpv_energized),
                    IGNITOR_IN: int(ignitor_energized),
                    PRE_PRESS_IN: int(pre_press_energized),
                    FUEL_PT_1_PRESSURE: random.normalvariate(true_fuel_pressure, 15),
                    FUEL_PT_2_PRESSURE: random.normalvariate(true_fuel_pressure, 15),
                    FUEL_PT_3_PRESSURE: random.normalvariate(true_fuel_pressure, 15),
                    OX_TANK_1_PRESSURE: random.normalvariate(true_ox_pressure, 15),
                    OX_TANK_2_PRESSURE: random.normalvariate(true_ox_pressure, 15),
                    OX_TANK_3_PRESSURE: random.normalvariate(true_ox_pressure, 15),
                    PRESS_TANK_PT_1: 3600
                    + random.normalvariate(true_press_pressure, 15),
                    PRESS_TANK_PT_2: 3600
                    + random.normalvariate(true_press_pressure, 15),
                    PRESS_TANK_PT_3: 3600
                    + random.normalvariate(true_press_pressure, 15),
                    OX_PRE_FILL_PT: 0,
                    OX_PRESS_DOME_PILOT_REG_PT: 0,
                    OX_PRESS_PT: 0,
                    OX_FLOWMETER_INLET_PT: 0,
                    OX_FLOWMETER_THROAT_PT: 0,
                    OX_LEVEL_SENSOR: 0,
                    FUEL_FLOWMETER_INLET_PT: 0,
                    FUEL_FLOWMETER_THROAT_PT: 0,
                    FUEL_LEVEL_SENSOR: 0,
                    TRICKLE_PURGE_POST_REG_PT: 0,
                    TRICKLE_PURGE_PRE_2K_PT: 0,
                    AIR_DRIVE_2K_PT: 0,
                    AIR_DRIVE_POST_REG_PT: 0,
                    PRESS_TANK_SUPPLY: supply_2k + random.uniform(-20, 20),
                    GAS_BOOSTER_OUTLET_PT: true_press_pressure,
                    PRESS_TANK_2K_BOTTLE_PRE_FILL_PT: 0,
                    PNEUMATICS_BOTTLE_PT: 0,
                    TRAILER_PNEMATICS_PT: 0,
                    ENGINE_PNEUMATICS_PT: 0,
                    PURGE_2K_BOTTLE_PT: 0,
                    PURGE_POST_REG_PT: 0,
                }

                i += 1
                if i % 50 == 0:
                    print(write_data)
                    print(len(write_data))

                writer.write(write_data)

            except Exception as e:
                print(e)
                raise e
