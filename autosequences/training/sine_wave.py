import synnax
import math
import time
import random
import sys

client = synnax.Synnax()

RATE = (synnax.Rate.HZ * 50).period.seconds
NOISE = False

if len(sys.argv) > 1:
    if sys.argv[1] == "noise" or sys.argv[1] == "Noise":
        NOISE = True
        print("Running with noise")
if not NOISE:
    print("Running without noise")
    

sine_time = client.channels.create(
    name="sinewave_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

sine_data = client.channels.create(
    name="sinewave_data",
    data_type=synnax.DataType.FLOAT32,
    index=sine_time.key,
    retrieve_if_name_exists=True
)

start = synnax.TimeStamp.now()
print(f"Starting sine wave generation at {start}")
i = 0

with client.open_writer(start=synnax.TimeStamp.now(), channels=[sine_time.name, sine_data.name], authorities=5, name="sine_wave.py") as writer:
    while True:
        writer.write({
            "sinewave_time": synnax.TimeStamp.now(),
            "sinewave_data": math.sin(i * math.pi / 100) + (random.normalvariate(0, 0.1) if NOISE else 0)
        })
        time.sleep(RATE)
        if i % 100 == 0:
            print(f"Generated {i} sine wave samples")
        i += 1