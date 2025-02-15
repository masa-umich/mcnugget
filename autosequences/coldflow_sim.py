import time
import random
import synnax as sy

client = sy.Synnax(
    host="localhost", port=9090, username="synnax", password="seldon", secure=False
)

GSE_TIME = "gse_time"

### PRESSURE TRANSDUCERS ###
PNEUMATICS_BOTTLE = "gse_pt_1"
TRAILER_PNEUMATICS = "gse_pt_2"
ENGINE_PNEUMATICS = "gse_pt_3"
PRESS_BOTTLE = "gse_pt_4"
OX_TPC_INLET = "gse_pt_5"
OX_PILOT_OUTLET = "gse_pt_6"
OX_DOME = "gse_pt_7"
OX_TPC_OUTLET = "gse_pt_8"
OX_FLOWMETER_INLET = "gse_pt_9"
OX_FLOWMETER_THROAT = "gse_pt_10"
OX_LEVEL_SENSOR = "gse_pt_11"
FUEL_FLOWMETER_INLET = "gse_pt_12"
FUEL_FLOWMETER_THROAT = "gse_pt_13"
MARGIN_2 = "gse_pt_14"
FUEL_TPC_INLET = "gse_pt_15"
FUEL_PILOT_OUTLET = "gse_pt_16"
FUEL_DOME = "gse_pt_17"
FUEL_TPC_OUTLET = "gse_pt_18"
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
    OX_TPC_INLET,
    OX_PILOT_OUTLET,
    OX_DOME,
    OX_TPC_OUTLET,
    OX_FLOWMETER_INLET,
    OX_FLOWMETER_THROAT,
    # MARGIN_1,
    FUEL_FLOWMETER_INLET,
    FUEL_FLOWMETER_THROAT,
    MARGIN_2,
    FUEL_TPC_INLET,
    FUEL_PILOT_OUTLET,
    FUEL_DOME,
    FUEL_TPC_OUTLET,
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
FUEL_PREPRESS = "gse_vlv_15"
FUEL_PREPRESS_STATE = "gse_state_15"
FUEL_PREVALVE = "gse_vlv_17"
FUEL_PREVALVE_STATE = "gse_state_17"
OX_MPV = "gse_vlv_11"
OX_MPV_STATE = "gse_state_11"
FUEL_MPV = "gse_vlv_12"
FUEL_MPV_STATE = "gse_state_12"
# TORCH_FEEDLINE_PURGE = "gse_vlv_13"
# TORCH_FEEDLINE_PURGE_STATE = "gse_state_13"
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
VALVES = [
    OX_RETURN_LINE,
    OX_FILL,
    OX_PREVALVE,
    OX_DRAIN,
    # OX_FEEDLINE_PURGE,
    OX_FILL_PURGE,
    OX_PRE_PRESS,
    MPV_PURGE,
    FUEL_PREPRESS,
    FUEL_PREVALVE,
    OX_MPV,
    FUEL_MPV,
    # TORCH_FEEDLINE_PURGE,
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
    # TORCH_FEEDLINE_PURGE_STATE,
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

### CHANNEL CREATION ###
daq_time = client.channels.create(
    data_type=sy.DataType.TIMESTAMP,
    name=GSE_TIME,
    is_index=True,
    retrieve_if_name_exists=True,
)

for pt in PTS:
    client.channels.create(
        data_type=sy.DataType.FLOAT32,
        name=pt,
        index=daq_time.key,
        retrieve_if_name_exists=True,
    )

for tc in THERMOCOUPLES:
    client.channels.create(
        data_type=sy.DataType.FLOAT32,
        name=tc,
        index=daq_time.key,
        retrieve_if_name_exists=True,
    )

for lc in LOAD_CELLS:
    client.channels.create(
        data_type=sy.DataType.FLOAT32,
        name=lc,
        index=daq_time.key,
        retrieve_if_name_exists=True,
    )

CMDS = []
STATES = []
for vlv in VALVES:
    vlv_time = client.channels.create(
        data_type=sy.DataType.TIMESTAMP,
        name=vlv + "_cmd_time",
        is_index=True,
        retrieve_if_name_exists=True,
    )
    vlv_cmd = client.channels.create(
        data_type=sy.DataType.UINT8,
        name=vlv,
        index=vlv_time.key,
        retrieve_if_name_exists=True,
    )
    vlv_state = client.channels.create(
        data_type=sy.DataType.UINT8,
        name=vlv.replace("vlv", "state"),
        index=daq_time.key,
        retrieve_if_name_exists=True,
    )
    CMDS.append(vlv_cmd.name)
    STATES.append(vlv_state.name)

rate = (sy.Rate.HZ * 50).period.seconds
print("sim rate: ", rate)

DAQ_STATE = {}
CLIENT_STATE = {}
for sensor in PTS + THERMOCOUPLES + LOAD_CELLS:
    DAQ_STATE[sensor] = 0
for v in STATES:
    DAQ_STATE[v] = 0
for v in NORMALLY_OPEN:
    DAQ_STATE[v.replace("vlv", "state")] = 1

press_2k_supply = 5000
fuel_inlet = 0
ox_inlet = 0
fuel_tank_true = 0
ox_tank_true = 0
fuel_feedline_upstream_section = 0
ox_feedline_upstream_section = 0
fuel_feedline_flowmeter_section = 0
ox_feedline_flowmeter_section = 0
fuel_feedline_downstream_section = 0
ox_feedline_downstream_section = 0
ox_return_line = 0
dewars = 300

READ_CHANNELS = CMDS
WRITE_CHANNELS = [GSE_TIME] + PTS + THERMOCOUPLES + LOAD_CELLS + STATES
print("WRITE_CHANNELS: ", WRITE_CHANNELS)
print(f"writing to {len(WRITE_CHANNELS)} channels: {WRITE_CHANNELS}")
print(f"reading from {len(READ_CHANNELS)} channels: {READ_CHANNELS}")

with client.open_streamer(READ_CHANNELS) as streamer:
    with client.open_writer(
        sy.TimeStamp.now(),
        channels=WRITE_CHANNELS,
        name="coldflow sim",
        enable_auto_commit=True,
    ) as writer:
        i = 0
        while True:
            try:
                time.sleep(rate)
                while True:
                    f = streamer.read(0)
                    if f is None:
                        break
                    for c in f.channels:
                        CLIENT_STATE[c] = f[c][-1]
                        # print("received ", c, f[c][-1])

                for cmd in CLIENT_STATE:
                    DAQ_STATE[cmd.replace("vlv", "state")] = int(CLIENT_STATE[cmd])

                ### flow logic ###
                ### PREPRESS ###
                if DAQ_STATE.get(OX_PRE_PRESS.replace("vlv", "state")):
                    ox_tank_true += 4
                
                if DAQ_STATE.get(FUEL_PREPRESS.replace("vlv", "state")):
                    fuel_tank_true += 4

                ### PRESS ###
                if DAQ_STATE.get(PRESS_ISO.replace("vlv", "state")):
                    if DAQ_STATE.get(FUEL_DOME_ISO.replace("vlv", "state")):
                        press_2k_supply -= 1
                        fuel_tank_true += 5
                        # print("pressurizing fuel tank")
                    if DAQ_STATE.get(OX_DOME_ISO.replace("vlv", "state")):
                        press_2k_supply -= 1
                        ox_tank_true += 5
                        # print("pressurizing ox tank")

                ### OX ###
                if not DAQ_STATE.get(OX_VENT.replace("vlv", "state")):
                    ox_tank_true -= 8
                    # print("venting ox tank")
                if (
                    not DAQ_STATE.get(OX_MPV.replace("vlv", "state"))
                ) and DAQ_STATE.get(OX_PREVALVE.replace("vlv", "state")):
                    ox_tank_true -= 6
                    # print("ox to feedline")

                ### FUEL ###
                if not DAQ_STATE.get(FUEL_VENT.replace("vlv", "state")):
                    fuel_tank_true -= 7
                    # print("venting fuel tank")
                if (
                    not DAQ_STATE.get(FUEL_MPV.replace("vlv", "state"))
                ) and DAQ_STATE.get(FUEL_PREVALVE.replace("vlv", "state")):
                    fuel_tank_true -= 6
                    # print("fuel to feedline")

                fuel_tank_true -= 1

                # no negative pressures plz ;-;
                if press_2k_supply < 0:
                    press_2k_supply = 0
                if fuel_tank_true < 0:
                    fuel_tank_true = 0
                if ox_tank_true < 0:
                    ox_tank_true = 0

                ### PRESSURE TRANSDUCERS ###
                DAQ_STATE[PRESS_BOTTLE] = press_2k_supply + random.uniform(-100, 100)
                DAQ_STATE[FUEL_TANK_1] = fuel_tank_true + random.uniform(-100, 100)
                DAQ_STATE[FUEL_TANK_2] = fuel_tank_true + random.uniform(-100, 100)
                DAQ_STATE[FUEL_TANK_3] = fuel_tank_true + random.uniform(-100, 100)
                DAQ_STATE[OX_TANK_1] = ox_tank_true + random.uniform(-100, 100)
                DAQ_STATE[OX_TANK_2] = ox_tank_true + random.uniform(-100, 100)
                DAQ_STATE[OX_TANK_3] = ox_tank_true + random.uniform(-100, 100)

                DAQ_STATE[GSE_TIME] = sy.TimeStamp.now()
                writer.write(DAQ_STATE)

                if i % 50 == 0:
                    print(len(DAQ_STATE), DAQ_STATE)
                    print("ox_dome_iso state: ", CLIENT_STATE.get(OX_DOME_ISO))
                    print("ox_vent state: ", CLIENT_STATE.get(OX_VENT))
                    print("ox_prevalve state: ", CLIENT_STATE.get(OX_PREVALVE))
                    print("ox_mpv state: ", CLIENT_STATE.get(OX_MPV))
                    print("fuel_dome_iso state: ", CLIENT_STATE.get(FUEL_DOME_ISO))
                    print("fuel_vent state: ", CLIENT_STATE.get(FUEL_VENT))
                    print("fuel_prevalve state: ", CLIENT_STATE.get(FUEL_PREVALVE))
                    print("fuel_mpv state: ", CLIENT_STATE.get(FUEL_MPV))
                    print("press_iso state: ", CLIENT_STATE.get(PRESS_ISO))
                i += 1

            except Exception as e:
                print(e)
                raise e
