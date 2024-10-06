import time
import random
import synnax

import synnax.control
# these are just some imports we will use

client = synnax.Synnax()

DEBUG = False

# sim index
SIM_TIME = "daq_time"

# valves
PRESS_VALVE_ACK = "gse_doa_1"
PRESS_VALVE_CMD = "gse_doc_1"
PRESS_VENT_ACK = "gse_doa_2"
PRESS_VENT_CMD = "gse_doc_2"

# PTs
PRESS_TANK = "gse_ai_1"
PRESS_TANK_1 = "gse_ai_9"
PRESS_TANK_2 = "gse_ai_10"
PRESS_TANK_3 = "gse_ai_11"
PRESS_SUPPLY = "gse_ai_2"

CMDS = [PRESS_VALVE_CMD, PRESS_VENT_CMD]
ACKS = [PRESS_VALVE_ACK, PRESS_VENT_ACK]
PTS = [PRESS_TANK, PRESS_SUPPLY]

# this channel keeps track of timestamps on the sim, which is committing data
sim_time = client.channels.create(
    name=SIM_TIME,
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
print(f"created/retrieved channel {SIM_TIME} with key", sim_time.key)

# this channel keeps track of timestamps for the press_valve channel, which is where we send commands
press_valve_time = client.channels.create(
    name=PRESS_VALVE_CMD + "_cmd_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
# print("created/retrieved channel press_valve_time with key", press_valve_time.key)

# this channel is a command channel to send commands from us to the sim
press_valve_cmd = client.channels.create(
    name=PRESS_VALVE_CMD,
    data_type=synnax.DataType.UINT8,
    index=press_valve_time.key,
    retrieve_if_name_exists=True,
)
print(f"created/retrieved channel {PRESS_VALVE_CMD} with key", press_valve_cmd.key)

# this channel is an acknowledgement channel to confirm commands are received
press_valve_ack = client.channels.create(
    name=PRESS_VALVE_ACK,
    data_type=synnax.DataType.UINT8,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)
print(f"created/retrieved channel {PRESS_VALVE_ACK} with key", press_valve_ack.key)

# this channel keeps track of timestamps for the press_vent channel, which is where we send commands
press_vent_time = client.channels.create(
    name=PRESS_VENT_CMD + "_cmd_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
# print("created/retrieved channel press_vent_time with key", press_vent_time.key)

# this channel is a command channel to send commands from us to the sim
press_vent_cmd = client.channels.create(
    name=PRESS_VENT_CMD,
    data_type=synnax.DataType.UINT8,
    index=press_vent_time.key,
    retrieve_if_name_exists=True,
)
print(f"created/retrieved channel {PRESS_VENT_CMD} with key", press_vent_cmd.key)

# this channel is an acknowledgement channel to confirm commands are received
press_vent_ack = client.channels.create(
    name=PRESS_VENT_ACK,
    data_type=synnax.DataType.UINT8,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)
print(f"created/retrieved channel {PRESS_VENT_ACK} with key", press_vent_ack.key)

press_tank_pt = client.channels.create(
    name=PRESS_TANK,
    data_type=synnax.DataType.FLOAT64,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)
print(f"created/retrieved channel {PRESS_TANK} with key", press_tank_pt.key)

for i in range(6, 9):
    press_tank_pt = client.channels.create(
        name=f"gse_ai_{i}",
        data_type=synnax.DataType.FLOAT64,
        index=sim_time.key,
        retrieve_if_name_exists=True,
    )
    print(f"created/retrieved channel gse_ai_{i} with key", press_tank_pt.key)

press_supply_pt = client.channels.create(
    name=PRESS_SUPPLY,
    data_type=synnax.DataType.FLOAT64,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)
print(f"created/retrieved channel {PRESS_SUPPLY} with key", press_supply_pt.key)

# this just specifies the rate at which we commit data
rate = (synnax.Rate.HZ * 50).period.seconds
print("rate: ", rate)
BURST = False

true_press_pressure = 0
true_supply_pressure = 2000
def noise(pressure):
    return pressure + random.uniform(-20, 20)

# Create DAQ_STATE dictionary
LOCAL_STATE = {
    PRESS_VALVE_ACK: 0,
    PRESS_VENT_ACK: 0,
    PRESS_SUPPLY: true_supply_pressure,
    PRESS_TANK_1: true_press_pressure,
    PRESS_TANK_2: true_press_pressure,
    PRESS_TANK_3: true_press_pressure,
    SIM_TIME: synnax.TimeStamp.now()
}

REMOTE_STATE = {
    PRESS_VALVE_CMD: 0,
    PRESS_VENT_CMD: 0,
}

READ_FROM = list(REMOTE_STATE)
WRITE_TO = list(LOCAL_STATE)
print(f"reading from {READ_FROM}")
print(f"writing to {WRITE_TO}")

with client.open_streamer(READ_FROM) as streamer:
    with client.open_writer(
        synnax.TimeStamp.now(),
        channels=WRITE_TO,
        name="basic_sim",
        enable_auto_commit=True
    ) as writer:
        i = 0  # for logging
        while True:
            time.sleep(rate)
            while True:
                f = streamer.read(0)
                if f is None:
                    break
                for c in f.channels:
                    if DEBUG:
                        print(f"setting {c} to {f[c][-1]}")
                    REMOTE_STATE[c] = f[c][-1]
        
            press_valve_energized = REMOTE_STATE[PRESS_VALVE_CMD] == 1
            press_vent_energized = REMOTE_STATE[PRESS_VENT_CMD] == 1

            if i % 100 == 0:
                print(f"cycle {i}")
            if DEBUG and i % 100 == 0:
                print(f"press_valve_energized:{press_valve_energized}")
                print(f"press_vent_energized:{press_vent_energized}")
                print(f"true_press_pressure:{true_press_pressure}")
                print(f"true_supply_pressure:{true_supply_pressure}")

            if press_valve_energized and true_supply_pressure > true_press_pressure:
                true_supply_pressure = max(0, true_supply_pressure - 0.3)
                true_press_pressure += 9

            if (not press_vent_energized) and true_press_pressure > 0:
                true_press_pressure = max(0, true_press_pressure - 1)
            
            if true_press_pressure < 0:
                raise Exception("You created negative pressure, this should not be allowed.")

            # drop pressure once it hits 1200 to simulate burst
            if BURST or true_press_pressure > 1200:
                if not BURST:
                    print("tank has burst")
                BURST = True
                true_press_pressure -= 40
                true_press_pressure = max(0, true_press_pressure)

            if true_press_pressure < 100 and BURST:
                print("tank has unburst :)")
                BURST = False

            now = synnax.TimeStamp.now()

            LOCAL_STATE[PRESS_VALVE_ACK] = REMOTE_STATE[PRESS_VALVE_CMD]
            LOCAL_STATE[PRESS_VENT_ACK] = REMOTE_STATE[PRESS_VENT_CMD]
            LOCAL_STATE[PRESS_SUPPLY] = noise(true_supply_pressure)
            LOCAL_STATE[PRESS_TANK_1] = noise(true_press_pressure)
            LOCAL_STATE[PRESS_TANK_2] = noise(true_press_pressure)
            LOCAL_STATE[PRESS_TANK_3] = noise(true_press_pressure)
            LOCAL_STATE[SIM_TIME] = synnax.TimeStamp.now()

            writer.write(LOCAL_STATE)
            writer.commit()
            i += 1
