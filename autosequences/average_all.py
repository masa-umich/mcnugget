import time
import synnax
import synnax.control
from collections import deque

client = synnax.Synnax()

channels_to_average = []
for pt in range(42):
    if pt == 13:
        continue
    channels_to_average.append(f"gse_pt_{pt + 1}")

average_channels = []
for pt in range(42):
    if pt == 13:
        continue
    average_channels.append(f"gse_pt_{pt + 1}_avg")

rate = (synnax.Rate.HZ * 50).period.seconds
print("rate: ", rate)

running_average_length = 25
print(f"averaging over {running_average_length * rate} seconds")

ai_channel = client.channels.retrieve("gse_pt_1")
ai_time = client.channels.retrieve("gse_ai_time")
print("ai_time.key: ", ai_time.key)

average_time = client.channels.create(
    name="average_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)
for pt in average_channels:
    client.channels.create(
        name=pt,
        data_type=synnax.DataType.FLOAT32,
        index=ai_time.key,
        retrieve_if_name_exists=True,
    )

AVERAGE_VALUES = {}
for chan in channels_to_average:
    AVERAGE_VALUES[chan] = deque()
SUMS = {}
for chan in channels_to_average:
    SUMS[chan] = 0
WRITE_DATA = {}

with client.control.acquire("average", read=channels_to_average + ["gse_ai_time"], write=[], write_authorities=30) as auto:
    with client.open_writer(synnax.TimeStamp.now(), average_channels + ["average_time"], 20) as writer:
        time.sleep(1)
        i = 0
        while True:
            for chan in channels_to_average:
                value = auto[chan]
                AVERAGE_VALUES[chan].append(value)
                SUMS[chan] += value
                if len(AVERAGE_VALUES[chan]) > running_average_length:
                    SUMS[chan] -= AVERAGE_VALUES[chan].popleft()
                average = SUMS[chan] / len(AVERAGE_VALUES[chan])
                WRITE_DATA[chan + "_avg"] = average
            # auto["gse_pt_1_avg"] = average
            # print("gse_ai_time: ", auto["gse_ai_time"])
            WRITE_DATA["average_time"] = auto["gse_ai_time"]
            if i % 50 == 0:
                # print("writing to: ", WRITE_DATA.keys())
                # print(WRITE_DATA)
                print(f"processed {i} samples")
            i += 1
            writer.write(
                WRITE_DATA
            )
            time.sleep(rate)