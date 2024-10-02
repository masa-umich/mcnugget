import time
import synnax
import synnax.control
from collections import deque
from mcnugget.autosequences import syauto

# this initializes a connection to the Synnax server
client = synnax.Synnax()

channels_to_average = [
    "gse_ai_6",
    "gse_ai_7",
    "gse_ai_8",
]

rate = (synnax.Rate.HZ * 50).period.seconds
running_average_values = {}
running_average_sums = {}
running_average_length = 10  # for 50Hz data, this is equivalent to 0.2 seconds

average_time = client.channels.create(
    name="average_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
print("created channel average_time with key", average_time.key)

daq_time = client.channels.create(
    name="daq_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
print("created channel daq_time with key", daq_time.key)


for channel in channels_to_average:
    base_channel = client.channels.create(
        name=channel,
        data_type=synnax.DataType.FLOAT64,
        index=daq_time.key,
        retrieve_if_name_exists=True
    )
    av_channel = client.channels.create(
        name=channel + "_avg",
        data_type=synnax.DataType.FLOAT64,
        index=average_time.key,
        retrieve_if_name_exists=True
    )
    print(f"created channel {channel} with key {base_channel.key}")
    print(f"created channel {channel}_avg with key {av_channel.key}")

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

READ_FROM = channels_to_average + ["daq_time"]
WRITE_TO = ["average_time"]
STATE = {}
for channel in channels_to_average:
    WRITE_TO.append(channel + "_avg")

print(f"reading from {READ_FROM}")
print(f"writing to {WRITE_TO}")
# with client.control.acquire(name="average.py", read=READ_FROM, write=WRITE_TO, write_authorities=255) as auto:
with client.open_streamer(READ_FROM) as streamer:
    with client.open_writer(
        synnax.TimeStamp.now(),
        channels = WRITE_TO,
        name="average.py",
        enable_auto_commit=True
    ) as writer:
        print("initializing...")
        print("averaging the following channels: ")
        for c in channels_to_average:
            print(c)
        time.sleep(2)
        try: 
            # i = 0
            while True:
                # STATE["average_time"] = auto["daq_time"]
                STATE["average_time"] = synnax.TimeStamp.now()
                while True:
                    frame = streamer.read(0)
                    if frame is None:
                        break
                    for ch in frame.channels:
                        if ch in channels_to_average:
                            update_average(frame[ch][-1], ch)

                for channel in channels_to_average:
                    STATE[channel + "_avg"] = read_average(channel)
                # i += 1
                # if i % 50 == 0:
                #     print(f"writing {STATE}")
                writer.write(STATE)
                time.sleep(rate)
        except Exception as e:
            print(e)
print("terminating")
time.sleep(2)