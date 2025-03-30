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

RATE = (synnax.Rate.HZ * 1000).period.seconds
print("rate: ", RATE)

running_average_length = 40
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
# with client.open_streamer(read_channels) as streamer:
with client.control.acquire("average script", read_channels, [], 5) as auto:
    with client.open_writer(synnax.TimeStamp.now(), write_channels, 20, enable_auto_commit=True) as writer:
        time.sleep(1)
        errors = 0
        iteration = 0
        while True:
            try:
                for chan in channels_to_average:
                    value = auto[chan]
                    AVERAGE_VALUES[chan].append(value)
                    SUMS[chan] += value
                    if len(AVERAGE_VALUES[chan]) > running_average_length:
                        SUMS[chan] -= AVERAGE_VALUES[chan].popleft()
                    average = SUMS[chan] / len(AVERAGE_VALUES[chan])
                    WRITE_DATA[chan + "_avg"] = average
                    WRITE_DATA["gse_average_time"] = auto["gse_ai_time"]
                time.sleep(RATE)
                writer.write(WRITE_DATA)

                if iteration % 6000 == 0:
                    print("iteration ", iteration)
                iteration += 1
                
            except KeyboardInterrupt:
                print("terminating script...")
                break

            # except Exception as e:
            #     print(f"encountered an error: {e}")
            #     errors += 1
            #     if errors > 5:
            #         print("too many errors, terminating script...")
            #         exit(1)