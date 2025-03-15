import time
import synnax
import synnax.control
from collections import deque

client = synnax.Synnax()

channels_to_average = []

average_time = client.channels.create(
    name="average_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

for pt in range(42):
    try:
        client.channels.retrieve(f"gse_pt_{pt}")
        client.channels.create(
            name=f"gse_pt_{pt}_avg",
            data_type=synnax.DataType.FLOAT32,
            index=average_time.key,
            retrieve_if_name_exists=True
        )
        channels_to_average.append(f"gse_pt_{pt}")
    except synnax.exceptions.NotFoundError:
        print(f"unable to find gse_pt_{pt}, excluding from channels to average")
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

read_channels = channels_to_average + ["gse_time"]
write_channels = list([c + "_avg" for c in channels_to_average]) + ["average_time"]
with client.open_streamer(read_channels) as streamer:
    with client.open_writer(synnax.TimeStamp.now(), write_channels, 20) as writer:
        errors = 0
        iteration = 0
        while True:
            try:
                frame = streamer.read()
                if frame is not None:
                    for chan in channels_to_average:
                        value = frame[chan][-1]
                        AVERAGE_VALUES[chan].append(value)
                        SUMS[chan] += value
                        if len(AVERAGE_VALUES[chan]) > running_average_length:
                            SUMS[chan] -= AVERAGE_VALUES[chan].popleft()
                        average = SUMS[chan] / len(AVERAGE_VALUES[chan])
                        WRITE_DATA[chan + "_avg"] = average
                    WRITE_DATA["average_time"] = frame["gse_time"]
                time.sleep(RATE)
                writer.write(WRITE_DATA)

                if iteration % 6000 == 0:
                    print("iteration ", iteration)
                iteration += 1
                
            except KeyboardInterrupt:
                print("terminating script...")
                exit(0)
            except Exception as e:
                print(f"encountered an error: {e}")
                errors += 1
                if errors > 5:
                    print("too many errors, terminating script...")
                    exit(1)