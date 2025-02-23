import time
import random
import synnax
import synnax.control
import math
import random

client = synnax.Synnax()

# valves
NITROUS_MPV_VLV = "gse_vlv_1"
NITROUS_MPV_STATE = "gse_state_1"
ETHANOL_MPV_VLV = "gse_vlv_2"
ETHANOL_MPV_STATE = "gse_state_2"
TORCH_PURGE_VLV = "gse_vlv_4"
TORCH_PURGE_STATE = "gse_state_4"
SPARK_VLV = "gse_vlv_6"
SPARK_STATE = "gse_state_6"
ALL_VLVS = [
    NITROUS_MPV_VLV,
    ETHANOL_MPV_VLV,
    TORCH_PURGE_VLV,
    SPARK_VLV,
]
ALL_STATES = [
    NITROUS_MPV_STATE,
    ETHANOL_MPV_STATE,
    TORCH_PURGE_STATE,
    SPARK_STATE,
]

# pressure transducers
NITROUS_SUPPLY = "gse_pt_1"
# NITROUS_POST_REG = "gse_pt_2"
TORCH_2K_BOTTLE = "gse_pt_3"
# TORCH_2K_POST_REG = "gse_pt_4"
ETHANOL_TANK = "gse_pt_5"
TORCH_PT_1 = "gse_pt_6"
TORCH_PT_2 = "gse_pt_7"
TORCH_PT_3 = "gse_pt_8"
ALL_PTS = [
    NITROUS_SUPPLY,
    TORCH_2K_BOTTLE,
    ETHANOL_TANK,
    TORCH_PT_1,
    TORCH_PT_2,
    TORCH_PT_3,
]

IGNITION = "torch_ignition"  # for sim purposes only

READ_FROM = ALL_VLVS
WRITE_TO = ALL_STATES + ALL_PTS + ["gse_ai_time", "gse_state_time", "torch_ignition"]

ai_time = client.channels.create(
    name="gse_ai_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

state_time = client.channels.create(
    name="gse_state_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

torch_ignition = client.channels.create(
    name="torch_ignition",
    data_type=synnax.DataType.UINT8,
    index=state_time.key,
    retrieve_if_name_exists=True,
)

for channel in ALL_VLVS:
    vlv_time = client.channels.create(
        name=channel + "_time",
        data_type=synnax.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True,
    )
    client.channels.create(
        name=channel,
        data_type=synnax.DataType.UINT8,
        index=vlv_time.key,
        retrieve_if_name_exists=True,
    )

for channel in ALL_STATES:
    client.channels.create(
        name=channel,
        data_type=synnax.DataType.UINT8,
        index=state_time.key,
        retrieve_if_name_exists=True,
    )

for channel in ALL_PTS:
    client.channels.create(
        name=channel,
        data_type=synnax.DataType.FLOAT64,
        index=ai_time.key,
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

ETHANOL_REG = 450
LAST_IGNITION = synnax.TimeStamp.now()

TRUE_VALUES = {pt: 0 for pt in ALL_PTS}
TRUE_VALUES[TORCH_2K_BOTTLE] = 2000
TRUE_VALUES[NITROUS_SUPPLY] = 1000
TRUE_VALUES[ETHANOL_TANK] = 10000
TRUE_VALUES["chamber_nitrous"] = 0
TRUE_VALUES["chamber_ethanol"] = 0
TRUE_VALUES["chamber_pressure"] = 0
TRUE_VALUES["chamber_spark"] = False

print(f"reading from {len(READ_FROM)} channels")
print(f"writing to {len(WRITE_TO)} channels")


def ignition(state):
    if random.random() > 0.99999:
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
            if (
                TRUE_VALUES[TORCH_2K_BOTTLE] > 0
                and TRUE_VALUES[TORCH_2K_BOTTLE] > ETHANOL_REG
                and TRUE_VALUES[ETHANOL_TANK] < ETHANOL_REG
            ):
                TRUE_VALUES[TORCH_2K_BOTTLE] -= 2
                TRUE_VALUES[ETHANOL_TANK] += 2

            # ethanol
            if WRITE_STATE[ETHANOL_MPV_STATE] == 1 and TRUE_VALUES[ETHANOL_TANK] > 0:
                TRUE_VALUES[ETHANOL_TANK] -= 2
                TRUE_VALUES["chamber_ethanol"] += 3

            # vent
            if TRUE_VALUES[ETHANOL_TANK] > 0:
                TRUE_VALUES[ETHANOL_TANK] -= 4

            # spark
            TRUE_VALUES["chamber_spark"] = WRITE_STATE[SPARK_STATE] == 1

            # purge

            # flowmeters

            # filter out negatives in TRUE_VALUES
            for key in TRUE_VALUES:
                TRUE_VALUES[key] = max(0, TRUE_VALUES[key])

            ignition_ = ignition(TRUE_VALUES)
            if ignition_:
                TRUE_VALUES["chamber_pressure"] = 700 + (random.random() - 0.5) * 200
                LAST_IGNITION = synnax.TimeStamp.now()

            if synnax.TimeStamp.now() - LAST_IGNITION > synnax.TimeSpan(3 * 10**9):
                TRUE_VALUES["chamber_pressure"] = 0

            # randomize
            WRITE_STATE[ETHANOL_TANK] = TRUE_VALUES[
                ETHANOL_TANK
            ] + random.normalvariate(-30, 30)
            WRITE_STATE[NITROUS_SUPPLY] = TRUE_VALUES[
                NITROUS_SUPPLY
            ] + random.normalvariate(-30, 30)
            WRITE_STATE[TORCH_2K_BOTTLE] = TRUE_VALUES[
                TORCH_2K_BOTTLE
            ] + random.normalvariate(-30, 30)
            WRITE_STATE[TORCH_PT_1] = TRUE_VALUES[
                "chamber_pressure"
            ] + random.normalvariate(-30, 30)
            WRITE_STATE[TORCH_PT_2] = TRUE_VALUES[
                "chamber_pressure"
            ] + random.normalvariate(-30, 30)
            WRITE_STATE[TORCH_PT_3] = TRUE_VALUES[
                "chamber_pressure"
            ] + random.normalvariate(-30, 30)
            WRITE_STATE["torch_ignition"] = ignition_
            WRITE_STATE["gse_ai_time"] = synnax.TimeStamp.now()
            WRITE_STATE["gse_state_time"] = WRITE_STATE["gse_ai_time"]

            # write to channels
            writer.write(WRITE_STATE)
