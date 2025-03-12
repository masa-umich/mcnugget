import synnax
import datetime
import matplotlib.pyplot as plt
import numpy as np

client = synnax.Synnax() # use `synnax login` command for this to work

RANGE_NAME = "local_testing_range"

# year, month, day, hour, minute, second
RANGE_START: datetime.datetime = datetime.datetime(2025, 3, 12, 18, 8, 0)
RANGE_END: datetime.datetime = datetime.datetime(2025, 3, 12, 18, 9, 0)

CHANNELS = [
    "range_time",
    "range_data"
]

DESTINATION_FILE = "range_data.csv"

synnax_range_start = synnax.TimeStamp(RANGE_START)
synnax_range_end = synnax.TimeStamp(RANGE_END)

print(f"starting range at {synnax_range_start}")
print(f"ending range at {synnax_range_end}")

range_time = client.channels.create(
    name="range_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

range_data = client.channels.create(
    name="range_data",
    data_type=synnax.DataType.FLOAT64,
    index=range_time.key,
    retrieve_if_name_exists=True
)

sy_range = client.ranges.create(
    name=RANGE_NAME,
    time_range=synnax.TimeRange(synnax_range_start, synnax_range_end),
    retrieve_if_name_exists=True,
)

if sy_range.time_range.start != synnax_range_start or sy_range.time_range.end != synnax_range_end:
    print("A different range with the same name already exists, please be more creative.")
    exit(1)
else:
    print("Successfully created or retrieved range")

"""
As of 3/12, there is a bug in synnax where you can only retrieve range data 
if it was written from the same client. So, we will provide the data we 
want to retrieve here.
"""

time_data = np.linspace(synnax_range_start, synnax_range_end, 1000)
data = np.sin(time_data - synnax_range_start)

print(len(time_data))
print(len(data))
# print(time_data)
# print(data)

range_time.write(synnax_range_start, time_data)
range_data.write(synnax_range_start, data)

print("Successfully wrote ghost data.")

with open(DESTINATION_FILE, "w") as file:
    # for i in range(len(example_range["create_range_data"])):
    #     file.write(f"{example_range['create_range_time'][i]},{example_range['create_range_data'][i]}\n")
    print(f"len(sy_range['range_data']): {len(sy_range['range_data'])}")
    for i in range(len(sy_range["range_data"])):
        file.write(f"{sy_range['range_data'][i]},{sy_range['range_time'][i]}\n")

    # for i in range(len(sy_range[CHANNELS[0]])):
    #     file.write([sy_range[channel][i] for channel in CHANNELS].join('\t') + '\n')

print(f"Finished writing data to {DESTINATION_FILE}")