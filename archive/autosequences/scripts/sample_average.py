import time
import synnax
import synnax.control
from collections import deque

client = synnax.Synnax()

channels_to_average = []

average_time = client.channels.create(
    name="gse_average_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

for pt in range(42):
    try:
        client.channels.retrieve(f"gse_pt_{pt + 1}")
        client.channels.create(
            name=f"gse_pt_{pt + 1}_avg",
            data_type=synnax.DataType.FLOAT32,
            index=average_time.key,
            retrieve_if_name_exists=True
        )
        channels_to_average.append(f"gse_pt_{pt + 1}")
    except synnax.exceptions.NotFoundError:
        print(f"unable to find gse_pt_{pt + 1}, excluding from channels to average")
        continue

for lc in range(3):
    try:
        client.channels.retrieve(f"gse_lc_{lc + 1}")
        client.channels.create(
            name=f"gse_lc_{lc + 1}_avg",
            data_type=synnax.DataType.FLOAT32,
            index=average_time.key,
            retrieve_if_name_exists=True
        )
        channels_to_average.append(f"gse_lc_{lc + 1}")
    except synnax.exceptions.NotFoundError:
        print(f"unable to find gse_lc_{lc + 1}, excluding from channels to average")
        continue

RATE = (synnax.Rate.HZ * 100).period.seconds
print("rate: ", RATE)

running_average_length = 25
print(f"averaging over {running_average_length * RATE} seconds")

AVERAGE_VALUES = {}
for chan in channels_to_average:
    AVERAGE_VALUES[chan] = deque()
SUMS = {}
for chan in channels_to_average:
    SUMS[chan] = 0
WRITE_DATA = {}

read_channels = channels_to_average + ["gse_ai_time"]
write_channels = list([c + "_avg" for c in channels_to_average]) + ["gse_average_time"]
with client.open_streamer(read_channels) as streamer:
# with client.control.acquire("average script", read_channels, [], 5) as auto:
    initial_frame = streamer.read(1)
    if initial_frame is None:
        print("unable to stream data")
        exit(1)
    starting_time = initial_frame["gse_ai_time"][-1]
    with client.open_writer(starting_time, write_channels, 20, enable_auto_commit=True) as writer:
        # time.sleep(1)
        errors = 0
        iteration = 0
        while True:
            try:
                frame = streamer.read()
                if frame is None:
                    continue
                averages = {}
                for chan in channels_to_average:
                    averages[chan + "_avg"] = []
                    for sample in frame[chan]:
                        if len(AVERAGE_VALUES[chan]) >= running_average_length:
                            SUMS[chan] -= AVERAGE_VALUES[chan].popleft()
                        AVERAGE_VALUES[chan].append(sample)
                        SUMS[chan] += sample
                        averages[chan + "_avg"].append(SUMS[chan] / len(AVERAGE_VALUES[chan]))
                averages["gse_average_time"] = []
                for i in frame["gse_ai_time"]:
                    averages["gse_average_time"].append(i)

                writer.write(averages)

                if iteration % 60 == 0:
                    print("iteration ", iteration)
                iteration += 1

                time.sleep(0.0001)
                
            except KeyboardInterrupt:
                print("terminating script...")
                break
