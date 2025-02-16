import time
import synnax
import synnax.control
from collections import deque

client = synnax.Synnax()

channels_to_average = ["gse_ai_1"]

rate = (synnax.Rate.HZ * 50).period.seconds
print("rate: ", rate)

running_average_values = deque()
running_average_length = 25

ai_channel = client.channels.retrieve("gse_pt_1")
ai_time = client.channels.retrieve("gse_ai_time")
print("ai_time.key: ", ai_time.key)

average_time = client.channels.create(
    name="average_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)
average_channel = client.channels.create(
    name="gse_pt_1_avg",
    data_type=synnax.DataType.FLOAT32,
    index=average_time.key,
    retrieve_if_name_exists=True,
)

with client.control.acquire("average", read=["gse_pt_1", "gse_ai_time"], write=["gse_pt_1_avg", "average_time"], write_authorities=30) as auto:
    time.sleep(1)
    while True:
        value = auto["gse_pt_1"]
        running_average_values.append(value)
        if len(running_average_values) > running_average_length:
            running_average_values.popleft()
        average = sum(running_average_values) / len(running_average_values)
        WRITE_DATA = {
            "gse_pt_1_avg": average,
            "average_time": synnax.TimeStamp(auto["gse_ai_time"])
        }
        auto["gse_pt_1_avg"] = average
        # print("gse_ai_time: ", auto["gse_ai_time"])
        time.sleep(rate)