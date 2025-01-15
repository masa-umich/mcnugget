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
OX_FILL = "gse_vlv_2"
OX_PREVALVE = "gse_vlv_3"
OX_DRAIN = "gse_vlv_4"
OX_FEEDLINE_PURGE = "gse_vlv_5"
OX_FILL_PURGE = "gse_vlv_6"
OX_PRE_PRESS = "gse_vlv_7"
FUEL_FEEDLINE_PURGE = "gse_vlv_8"
FUEL_FILL = "gse_vlv_9"
FUEL_PREVALVE = "gse_vlv_10"
OX_MPV = "gse_vlv_11"
FUEL_MPV = "gse_vlv_12"
TORCH_FEEDLINE_PURGE = "gse_vlv_13"
TORCH_ETHANOL_PRESS_ISO = "gse_vlv_14"
TORCH_ETHANOL_TANK_VENT = "gse_vlv_15"
MARGIN_3 = "gse_vlv_16"
TORCH_ETHANOL_MPV = "gse_vlv_17"
TORCH_NITROUS_MPV = "gse_vlv_18"
TORCH_SPARK_PLUG = "gse_vlv_19"
PRESS_ISO = "gse_vlv_20"
FUEL_DOME_ISO = "gse_vlv_21"
OX_DOME_ISO = "gse_vlv_22"
OX_VENT = "gse_vlv_23"
FUEL_VENT = "gse_vlv_24"
VALVES = [
    OX_RETURN_LINE,
    OX_FILL,
    OX_PREVALVE,
    OX_DRAIN,
    OX_FEEDLINE_PURGE,
    OX_FILL_PURGE,
    OX_PRE_PRESS,
    FUEL_FEEDLINE_PURGE,
    FUEL_FILL,
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
                        print("received ", c, f[c][-1])

                for cmd in CLIENT_STATE:
                    DAQ_STATE[cmd.replace("vlv", "state")] = int(CLIENT_STATE[cmd])

                ### flow logic ###
                ### PRESS ###
                if CLIENT_STATE.get(PRESS_ISO):
                    if FUEL_DOME_ISO:
                        press_2k_supply -= 1
                        fuel_tank_true += 5
                    if OX_DOME_ISO:
                        press_2k_supply -= 1
                        ox_tank_true += 5

                ### OX ###
                if CLIENT_STATE.get(OX_VENT):
                    ox_tank_true -= 8
                if CLIENT_STATE.get(OX_MPV) and CLIENT_STATE.get(OX_PREVALVE):
                    ox_tank_true -= 6

                ### FUEL ###
                if CLIENT_STATE.get(FUEL_VENT):
                    fuel_tank_true -= 7
                if CLIENT_STATE.get(FUEL_MPV) and CLIENT_STATE.get(FUEL_PREVALVE):
                    fuel_tank_true -= 6

                ### PRESSURE TRANSDUCERS ###
                DAQ_STATE[PNEUMATICS_BOTTLE] = press_2k_supply + random.uniform(
                    -100, 100
                )

                DAQ_STATE[GSE_TIME] = sy.TimeStamp.now()
                writer.write(DAQ_STATE)

                if i % 50 == 0:
                    print(len(DAQ_STATE), DAQ_STATE)
                i += 1

            except Exception as e:
                print(e)
                raise e
