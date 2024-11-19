import time
import random
import synnax
import synnax.control
import math
import random

client = synnax.Synnax()

# valves
NITROUS_MPV_VLV = "torch_vlv_0"
NITROUS_MPV_STATE = "torch_state_0"
ETHANOL_MPV_VLV = "torch_vlv_1"
ETHANOL_MPV_STATE = "torch_state_1"
ETHANOL_PRESS_VLV = "torch_vlv_2"
ETHANOL_PRESS_STATE = "torch_state_2"
ETHANOL_VENT_VLV = "torch_vlv_3"
ETHANOL_VENT_STATE = "torch_state_3"
TORCH_PURGE_VLV = "torch_vlv_4"
TORCH_PURGE_STATE = "torch_state_4"
SPARK_VLV = "torch_vlv_5"
SPARK_STATE = "torch_state_5"
ALL_VLVS = [
    NITROUS_MPV_VLV,
    ETHANOL_MPV_VLV,
    ETHANOL_PRESS_VLV,
    ETHANOL_VENT_VLV,
    TORCH_PURGE_VLV,
    SPARK_VLV,
]
ALL_STATES = [
    NITROUS_MPV_STATE,
    ETHANOL_MPV_STATE,
    ETHANOL_PRESS_STATE,
    ETHANOL_VENT_STATE,
    TORCH_PURGE_STATE,
    SPARK_STATE,
]

# pressure transducers
PRESS_SUPPLY = "torch_pt_0"
# PRESS_POSTREG = "torch_pt_1"
NITROUS_SUPPLY = "torch_pt_2"
# NITROUS_POSTREG = "torch_pt_3"
ETHANOL_TANK = "torch_pt_4"
NITROUS_FLOWMETER = "torch_pt_5"
ETHANOL_FLOWMETER = "torch_pt_6"
TORCH_PT_1 = "torch_pt_7"
TORCH_PT_2 = "torch_pt_8"
TORCH_PT_3 = "torch_pt_9"
ALL_PTS = [
    PRESS_SUPPLY,
    # PRESS_POSTREG,
    NITROUS_SUPPLY,
    # NITROUS_POSTREG,
    ETHANOL_TANK,
    NITROUS_FLOWMETER,
    ETHANOL_FLOWMETER,
    TORCH_PT_1,
    TORCH_PT_2,
    TORCH_PT_3,
]

IGNITION = "torch_ignition"

READ_FROM = ALL_VLVS
WRITE_TO = ALL_STATES + ALL_PTS + ["torch_sim_time", "torch_ignition"]
CHANNELS = {}

sim_time = client.channels.create(
    name="torch_sim_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)
CHANNELS["torch_sim_time"] = sim_time

torch_ignition = client.channels.create(
    name="torch_ignition",
    data_type=synnax.DataType.UINT8,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)
CHANNELS["torch_ignition"] = torch_ignition

for channel in ALL_VLVS:
    CHANNELS[channel + "_VLV_time"] = client.channels.create(
        name=channel + "_VLV_time",
        data_type=synnax.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True,
    )
    CHANNELS[channel] = client.channels.create(
        name=channel,
        data_type=synnax.DataType.UINT8,
        index=CHANNELS[channel + "_VLV_time"].key,
        retrieve_if_name_exists=True,
    )

for channel in ALL_STATES:
    CHANNELS[channel] = client.channels.create(
        name=channel,
        data_type=synnax.DataType.UINT8,
        index=CHANNELS["torch_sim_time"].key,
        retrieve_if_name_exists=True,
    )

for channel in ALL_PTS:
    CHANNELS[channel] = client.channels.create(
        name=channel,
        data_type=synnax.DataType.FLOAT64,
        index=CHANNELS["torch_sim_time"].key,
        retrieve_if_name_exists=True,
    )

rate = (synnax.Rate.HZ * 50).period.seconds
print(f"rate: {rate}")

READ_STATE = {}
WRITE_STATE = {}
for channel in READ_FROM:
    READ_STATE[channel] = 0
for channel in WRITE_TO:
    WRITE_STATE[channel] = 0

TRUE_VALUES = {
    pt: 0 for pt in ALL_PTS
}
TRUE_VALUES[PRESS_SUPPLY] = 2000
TRUE_VALUES[NITROUS_SUPPLY] = 1000
TRUE_VALUES[ETHANOL_TANK] = 0
TRUE_VALUES["chamber_nitrous"] = 0
TRUE_VALUES["chamber_ethanol"] = 0
TRUE_VALUES["chamber_pressure"] = 0
TRUE_VALUES["chamber_spark"] = False

print(f"reading from {len(READ_FROM)} channels")
print(f"writing to {len(WRITE_TO)} channels")

def ignition(state):
    if random.random() > 0.1:
        return 0
    if state["chamber_nitrous"] < 10:
        return 0
    if state["chamber_ethanol"] < 10:
        return 0
    if state["chamber_spark"] == False:
        return 0
    return 1

with client.open_streamer(READ_FROM) as streamer:
    with client.open_writer(
        synnax.TimeStamp.now(),
        channels=WRITE_TO,
        name="torch_sim",
        enable_auto_commit=True,
    ) as writer:
        i = -1
        while True:
            i += 1
            time.sleep(rate)
            while True:
                f = streamer.read(0)
                if f is None:
                    break
                for c in f.channels:
                    if c in READ_FROM:
                        READ_STATE[c] = f[c][-1]

            # this sets the state based on received valves
            for channel in ALL_VLVS:
                WRITE_STATE[channel.replace("_vlv", "_state")] = READ_STATE[channel]

            # nitrous
            if WRITE_STATE[NITROUS_MPV_STATE] == 1 and TRUE_VALUES[NITROUS_SUPPLY] > 0:
                TRUE_VALUES[NITROUS_SUPPLY] -= 2
                TRUE_VALUES["chamber_nitrous"] += 3

            # press
            if WRITE_STATE[ETHANOL_PRESS_STATE] == 1 and TRUE_VALUES[PRESS_SUPPLY] > 0:
                TRUE_VALUES[PRESS_SUPPLY] -= 2
                TRUE_VALUES[ETHANOL_TANK] += 2

            # ethanol
            if WRITE_STATE[ETHANOL_MPV_STATE] == 1 and TRUE_VALUES[ETHANOL_TANK] > 0:
                TRUE_VALUES[ETHANOL_TANK] -= 2
                TRUE_VALUES["chamber_ethanol"] += 3

            # vent
            if WRITE_STATE[ETHANOL_VENT_STATE] == 0 and TRUE_VALUES[ETHANOL_TANK] > 0:
                TRUE_VALUES[ETHANOL_TANK] -= 4

            # spark
            TRUE_VALUES["chamber_spark"] = WRITE_STATE[SPARK_STATE] == 1

            # purge
            if WRITE_STATE[TORCH_PURGE_STATE] == 1:
                TRUE_VALUES[PRESS_SUPPLY] -= 4
                TRUE_VALUES["chamber_ethanol"] -= 6
                TRUE_VALUES["chamber_nitrous"] -= 6

            # flowmeters

            # filter out negatives in TRUE_VALUES
            for key in TRUE_VALUES:
                TRUE_VALUES[key] = max(0, TRUE_VALUES[key])

            ignition_ = ignition(TRUE_VALUES)
            if ignition_:
                TRUE_VALUES["chamber_pressure"] \
                    = 700 + (random.random() - 0.5) * 200
            
            #randomize
            WRITE_STATE[ETHANOL_TANK] = TRUE_VALUES[ETHANOL_TANK] + random.normalvariate(-30, 30)
            WRITE_STATE[NITROUS_SUPPLY] = TRUE_VALUES[NITROUS_SUPPLY] + random.normalvariate(-30, 30)
            WRITE_STATE[PRESS_SUPPLY] = TRUE_VALUES[PRESS_SUPPLY] + random.normalvariate(-30, 30)
            WRITE_STATE[TORCH_PT_1] = TRUE_VALUES["chamber_pressure"] + random.normalvariate(-30, 30)
            WRITE_STATE[TORCH_PT_2] = TRUE_VALUES["chamber_pressure"] + random.normalvariate(-30, 30)
            WRITE_STATE[TORCH_PT_3] = TRUE_VALUES["chamber_pressure"] + random.normalvariate(-30, 30)
            WRITE_STATE["torch_ignition"] = ignition_
            WRITE_STATE["torch_sim_time"] = synnax.TimeStamp.now()

            # write to channels
            writer.write(WRITE_STATE)
