import time
import random
import synnax
import math

import synnax.control
# these are just some imports we will use

client = synnax.Synnax()

DEBUG = False

# sim index
SIM_TIME = "sim_time"

# valves
SINE = "sine_wave"

# this channel keeps track of timestamps on the sim, which is committing data
sim_time = client.channels.create(
    name=SIM_TIME,
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

# this channel keeps track of timestamps for the press_valve channel, which is where we send commands
sine_wave = client.channels.create(
    name=SINE,
    data_type=synnax.DataType.FLOAT64,
    index=sim_time.key,
    retrieve_if_name_exists=True
)

rate = (synnax.Rate.HZ * 50).period.seconds
true_val = 0
def noise(pressure):
    return pressure + random.uniform(-30, 30)

with client.open_writer(
    synnax.TimeStamp.now(),
    channels=[SINE, "sim_time"],
    name="sine_wave",
    enable_auto_commit=True
) as writer:
    i = 0  # for logging
    while True:
        time.sleep(rate)
        # true_val = 500 * math.sin(i / 100 * math.pi)
        true_val = i
        # writer.write({"sine_wave": noise(true_val),
        writer.write({"sine_wave": true_val,
                      "sim_time": synnax.TimeStamp.now()})
        i += 1
