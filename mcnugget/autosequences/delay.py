import time
import synnax
import synnax.control
from collections import deque
from mcnugget.autosequences import syauto

# this initializes a connection to the Synnax server
client = synnax.Synnax()

channels_to_delay = [
    "gse_ai_9_avg",
    "gse_ai_10_avg",
    "gse_ai_11_avg"
]

rate = (synnax.Rate.HZ * 50).period.seconds
print("rate: ", rate)
values = {}
delay_in_samples = 20  # for 50Hz data, this is equivalent to 0.2 seconds

daq_time = client.channels.create(
    name="daq_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
print("created/retrieved channel daq_time with key", daq_time.key)

delay_time = client.channels.create(
    name="delay_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
print("created/retrieved channel delay_time with key", delay_time.key)


for channel in channels_to_delay:
    base_channel = client.channels.create(
        name=channel,
        data_type=synnax.DataType.FLOAT64,
        index=daq_time.key,
        retrieve_if_name_exists=True
    )
    av_channel = client.channels.create(
        name=channel + "_delay",
        data_type=synnax.DataType.FLOAT64,
        index=delay_time.key,
        retrieve_if_name_exists=True
    )
    print(f"created/retrieved channel {channel} with key {base_channel.key}")
    print(f"created/retrieved channel {channel}_delay with key {av_channel.key}")

def read_delay(channel: str):
    return values[channel][0]

def update_values(value: float, channel: str):
    new_value = value
    
    # if the channel is not present in the dictionary, add it
    if not values.get(channel):
        values[channel] = deque()
        
    values[channel].append(new_value)

    if len(values[channel]) > delay_in_samples:
        # delete the first value
        values[channel].popleft()

STATE = {}
READ_FROM = channels_to_delay
WRITE_TO = ["delay_time"]
for channel in channels_to_delay:
    WRITE_TO.append(channel + "_delay")
# READ_FROM.append("daq_time")

print(f"reading from {READ_FROM}")
print(f"writing to {WRITE_TO}")
print(f"delaying the following channels by {delay_in_samples} samples: ")
for c in channels_to_delay:
    print(c)

streamer = client.open_streamer(READ_FROM)
writer = client.open_writer(
        synnax.TimeStamp.now(),
        channels = WRITE_TO,
        name="delay.py",
        enable_auto_commit=True
    )

i = 0
try:
    print("initializing...")
    time.sleep(1)
    while True:
        i += 1
        if i % 100 == 0:
            print(f"cycle {i}")
        frame = streamer.read(0)
        streamer.read
        if frame is None:
            # print("frame is None")
            time.sleep(rate)
            continue
        for channel in READ_FROM:
            if not channel in frame:
                print(f"channel {channel} not found in frame")
                continue
            update_values(frame[channel][-1], channel)
            STATE[channel + "_delay"] = read_delay(channel)
        STATE["delay_time"] = synnax.TimeStamp.now() - synnax.TimeSpan(1000000000 * 3.3)
        writer.write(STATE)
        time.sleep(rate)

except KeyboardInterrupt:
    print("terminating")
    time.sleep(2)
    writer.close()
    streamer.close()
    client.close()
    print("terminated")
    exit()
