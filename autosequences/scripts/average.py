import time
import synnax
import synnax.control
from collections import deque

# this initializes a connection to the Synnax server
client = synnax.Synnax()

channels_to_average = ["gse_ai_1"]

rate = (synnax.Rate.HZ * 50).period.seconds
print("rate: ", rate)
running_average_values = {}
running_average_sums = {}
running_average_length = 10  # for 50Hz data, this is equivalent to 0.2 second

gse_ai_time = client.channels.retrieve(1048699)

average_time = client.channels.create(
    name="average_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

for channel in channels_to_average:
    base_channel = client.channels.create(
        name=channel,
        data_type=synnax.DataType.FLOAT32,
        index=gse_ai_time.key,
        retrieve_if_name_exists=True,
    )
    av_channel = client.channels.create(
        name=channel + "_avg",
        data_type=synnax.DataType.FLOAT32,
        index=average_time.key,
        retrieve_if_name_exists=True,
    )

def read_average(channel: str):
    return running_average_sums[channel] / len(running_average_values[channel])

def write_average(auto: synnax.control.Controller, channel: str):
    # print(f"{channel}_avg, {read_average(channel)}")
    write_channel = channel + "_avg"
    auto[write_channel] = read_average(channel)


def update_average(value: float, channel: str):
    # read in the most recent value
    # new_value = auto[channel]
    new_value = value

    # if the channel is not present in the dictionary, add it
    if not running_average_values.get(channel):
        running_average_values[channel] = deque()
        running_average_sums[channel] = 0

    running_average_sums[channel] += new_value
    running_average_values[channel].append(new_value)

    if len(running_average_values[channel]) > running_average_length:
        # update the sum, and delete the first value
        running_average_sums[channel] -= running_average_values[channel].popleft()


STATE = {}
READ_FROM = channels_to_average
WRITE_TO = ["average_time"]
for channel in channels_to_average:
    # STATE[channel + "_avg"] = -1
    WRITE_TO.append(channel + "_avg")
# READ_FROM.append("daq_time")

print(f"reading from {READ_FROM}")
print(f"writing to {WRITE_TO}")
print("averaging the following channels: ")
for c in channels_to_average:
    print(c)

with client.open_streamer(READ_FROM) as streamer:
    with client.open_writer(
        synnax.TimeStamp.now(),
        channels=WRITE_TO,
        name="average.py",
        enable_auto_commit=True
    ) as writer:
        TIME = synnax.TimeStamp.now()
        i = 0
        print("initializing...")
        time.sleep(1)
        while True:
            time.sleep(rate)
            f = streamer.read(0)
            if f is not None:
                for c in f.channels:
                    if c == "daq_time":
                        TIME = f[c][-1]
                    else:
                        update_average(f[c][-1], c)
                        STATE[c + "_avg"] = read_average(c)
            STATE["average_time"] = TIME
            writer.write(STATE)
            if i % 100 == 0:
                print(STATE)
                print(f"iteration {i}")
            i += 1
            time.sleep(rate)
