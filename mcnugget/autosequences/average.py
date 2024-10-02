import time
import synnax
import synnax.control
from collections import deque
from mcnugget.autosequences import syauto

# this initializes a connection to the Synnax server
client = synnax.Synnax()

channels_to_average = [
    "gse_ai_1",
    "gse_ai_2"
]

rate=1 / 50 # Hz
running_average_values = {}
running_average_sums = {}
running_average_length = 10  # for 50Hz data, this is equivalent to 0.2 seconds

average_time = client.channels.create(
    name="average_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

gse_time = client.channels.create(
    name="gse_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for channel in channels_to_average:
    client.channels.create(
        name=channel,
        data_type=synnax.DataType.FLOAT64,
        index=gse_time.key,
        retrieve_if_name_exists=True
    )
    client.channels.create(
        name=channel + "_avg",
        data_type=synnax.DataType.FLOAT64,
        index=average_time.key,
        retrieve_if_name_exists=True
    )

def read_average(channel: str):
    return running_average_sums[channel] / len(running_average_values[channel])
     
def write_average(auto: synnax.control.Controller, channel: str):
    write_channel = channel + "_avg"
    auto[write_channel] = read_average(channel)

def update_average(auto: synnax.control.Controller, channel: str):
    # read in the most recent value
    new_value = auto[channel]
    
    # if the channel is not present in the dictionary, add it
    if not running_average_values.get(channel):
        running_average_values[channel] = deque()
        running_average_sums[channel] = 0
        
    running_average_sums[channel] += new_value
    running_average_values[channel].append(new_value)

    if len(running_average_values[channel]) > running_average_length:
        # update the sum, and delete the first value
        running_average_sums[channel] -= running_average_values[channel].popleft()

READ_FROM = channels_to_average
WRITE_TO = []
for channel in channels_to_average:
    WRITE_TO.append(channel + "_avg")

with client.control.acquire(name="Demo Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=2) as auto:
    print("initializing...")
    print("averaging the following channels: ")
    for c in READ_FROM:
        print(c)
    time.sleep(2)
    try: 
        while True:
            for channel in channels_to_average:
                # print(f"averaging {channel}")
                update_average(auto, channel)
                write_average(auto, channel)
            time.sleep(rate)
    except Exception as e:
        print(e)
        print("terminating")
        time.sleep(1)
