import time
import random
import synnax as sy
# these are just some imports we will use

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)
# this initialized a connection to the Synnax server

# sim index
SIM_TIME = "sim_time"

# valves
PRESS_VALVE_ACK = "sim_doa_1"
PRESS_VALVE_CMD = "sim_doc_1"
PRESS_VENT_ACK = "sim_doa_2"
PRESS_VENT_CMD = "sim_doc_2"

# PTs
PRESS_TANK = "sim_ai_1"
PRESS_SUPPLY = "sim_ai_2"

CMDS = [PRESS_VALVE_CMD, PRESS_VENT_CMD]
ACKS = [PRESS_VALVE_ACK, PRESS_VENT_ACK]
PTS = [PRESS_TANK, PRESS_SUPPLY]

# this channel keeps track of timestamps on the sim, which is committing data
sim_time = client.channels.create(
    sy.Channel(
        name=SIM_TIME,
        data_type=sy.DataType.TIMESTAMP,
        is_index=True
    ),
    retrieve_if_name_exists=True
)

# this channel keeps track of timestamps for the press_valve channel, which is where we send commands
press_valve_time = client.channels.create(
    sy.Channel(
        name=PRESS_VALVE_CMD + "_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True
    ),
    retrieve_if_name_exists=True
)

# this channel is a command channel to send commands from us to the sim
press_valve_cmd = client.channels.create(
    sy.Channel(
        name=PRESS_VALVE_CMD,
        data_type=sy.DataType.UINT8,
        index=press_valve_time.key
    ),
    retrieve_if_name_exists=True,
)

# this channel is an acknowledgement channel to confirm commands are received
press_valve_ack = client.channels.create(
    sy.Channel(
        name=PRESS_VALVE_ACK,
        data_type=sy.DataType.UINT8,
        index=sim_time.key
    ),
    retrieve_if_name_exists=True,
)

# this channel keeps track of timestamps for the press_vent channel, which is where we send commands
press_vent_time = client.channels.create(
    sy.Channel(
        name=PRESS_VENT_CMD + "_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True
    ),
    retrieve_if_name_exists=True
)

# this channel is a command channel to send commands from us to the sim
press_vent_cmd = client.channels.create(
    sy.Channel(
        name=PRESS_VENT_CMD,
        data_type=sy.DataType.UINT8,
        index=press_vent_time.key
    ),
    retrieve_if_name_exists=True,
)

# this channel is an acknowledgement channel to confirm commands are received
press_vent_ack = client.channels.create(
    sy.Channel(
        name=PRESS_VENT_ACK,
        data_type=sy.DataType.UINT8,
        index=sim_time.key
    ),
    retrieve_if_name_exists=True,
)

press_tank_pt = client.channels.create(
    sy.Channel(
        name=PRESS_TANK,
        data_type=sy.DataType.FLOAT64,
        index=sim_time.key
    ),
    retrieve_if_name_exists=True,
)

press_supply_pt = client.channels.create(
    sy.Channel(
        name=PRESS_SUPPLY,
        data_type=sy.DataType.FLOAT64,
        index=sim_time.key
    ),
    retrieve_if_name_exists=True,
)

# this just specifies the rate at which we commit data
rate = (sy.Rate.HZ * 50).period.seconds

# Create DAQ_STATE dictionary
DAQ_STATE = {}

true_press_pressure = 0
true_supply_pressure = 2000
def noise(pressure):
    return pressure + random.uniform(-20, 20)


DAQ_STATE[PRESS_VALVE_ACK] = 0  # deenergized and closed
DAQ_STATE[PRESS_VALVE_CMD] = DAQ_STATE[PRESS_VALVE_ACK]
DAQ_STATE[PRESS_VENT_ACK] = 0  # deenergized and open
DAQ_STATE[PRESS_VENT_CMD] = DAQ_STATE[PRESS_VENT_ACK]
DAQ_STATE[PRESS_SUPPLY] = noise(true_supply_pressure)  # starting supply pressure
DAQ_STATE[PRESS_TANK] = noise(true_press_pressure)  # starting tank pressure
DAQ_STATE[SIM_TIME] = time.time()
DAQ_STATE[PRESS_SUPPLY] = true_supply_pressure
DAQ_STATE[PRESS_TANK] = true_press_pressure

READ_FROM = CMDS
WRITE_TO = ACKS + PTS + [SIM_TIME] + CMDS


with client.control.acquire(name="basic_sim", read=READ_FROM, write=WRITE_TO, write_authorities=2) as auto:
    # for channel in WRITE_TO:
    #     print(f"setting {channel} to {DAQ_STATE[channel]}")
    #     auto[channel] = DAQ_STATE[channel]
    # FILTERED_DAQ = {}
    # for k, v in DAQ_STATE.items():
    #     if k not in CMDS:
    #         FILTERED_DAQ[k] = v
    print(DAQ_STATE)
    auto._writer.write(DAQ_STATE)
    time.sleep(1)
    print(f"reading from {len(READ_FROM)} channels")
    print(f"writing to {len(WRITE_TO)} channels")
    i = 0  # commit stamp
    while True:
        try:
            for channel in READ_FROM:
                try:
                    time.sleep(rate)
                    DAQ_STATE[channel] = auto[channel]
                
                    press_valve_energized = DAQ_STATE[PRESS_VALVE_CMD] == 1
                    press_vent_energized = DAQ_STATE[PRESS_VENT_CMD] == 1

                    if press_valve_energized and true_supply_pressure > true_press_pressure:
                        true_supply_pressure -= 0.3
                        true_press_pressure += 0.9

                    if press_vent_energized and true_press_pressure < 0:
                        true_press_pressure -= 5
                    
                    if true_press_pressure < 0:
                        raise Exception("You created negative pressure, this should not be allowed.")

                    if true_press_pressure > 700:
                        raise Exception("You just blew up a press tank.")

                    now = sy.TimeStamp.now()

                    ok = auto.write({
                        SIM_TIME: now,
                        PRESS_VALVE_ACK: press_valve_energized,
                        PRESS_VENT_ACK: press_vent_energized,
                        PRESS_TANK: noise(true_press_pressure),
                        PRESS_SUPPLY: noise(true_supply_pressure)
                    })

                    i += 1
                    if (i % 80) == 0:
                        print(f"Committing {i} samples")
                        ok = auto.commit()
                        print(ok)
                    if (i % 320) == 0:
                        print("system state:")
                        for key, val in DAQ_STATE.items():
                            print(f"{key}:{val}")
                except:
                    # print(f"error during iteration {i}")
                    i += 1
        except Exception as e:
            print(e)
            raise e