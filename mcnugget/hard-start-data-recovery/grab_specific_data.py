import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt

keys = json.load(open("key_mappings.json"))
#TODO: replace this with your own data directory:
data_dir = "/Users/evanhekman/masa/var/lib/docker/volumes/deploy_synnax-data/_data/cesium"
output_dir = "output_data"

def read_in_channel(channel_key: str, sample_count: int=1620000):
    meta = json.load(open(os.path.join(data_dir, f"{channel_key}/meta.json")))
    data_type_ = meta["data_type"]

    # Set numpy data type according to the metadata
    if data_type_ == "float32":
        data_type = np.float32
    elif data_type_ == "uint8":
        data_type = np.uint8
    elif data_type_ == "timestamp":
        data_type = np.uint64
    else:
        raise ValueError(f"Unknown data type: {data_type_}")

    print(f"Processing {channel_key} as {data_type}")

    filepath = os.path.join(data_dir, f"{channel_key}/1.domain")

    try:
        # Open the file and read its contents from the beginning
        with open(filepath, "rb") as f:
            # Read the whole file as a numpy array
            data = np.fromfile(f, dtype=data_type)

        # Only keep the last `sample_count` elements
        if data.size > sample_count:
            data_to_save = data[-sample_count:]  # Slice the last `sample_count` elements
        else:
            data_to_save = data  # If the file is smaller than `sample_count`, keep all of it

        # Return data as a pandas Series for consistent indexing
        return pd.Series(data_to_save)

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return pd.Series()

def write_csv(data: pd.Series, channel_key: str):
    output_filepath = os.path.join(output_dir, f"{channel_key}.csv")
    data.to_csv(output_filepath, index=False)
    print(f"Data written to {output_filepath}")

def find_range(index_data: pd.Series, lower_bound: int, upper_bound: int):
    try:
        # Find the first index where the timestamp is greater than or equal to the lower bound
        filtered_data = index_data[(index_data >= lower_bound) & (index_data <= upper_bound)]

        if not filtered_data.empty:
            start_index = filtered_data.index[0]
            end_index = filtered_data.index[-1]
            print(f"Using data between the specified indices: {start_index} to {end_index}")
        else:
            print("No data found in the specified range.")
            start_index = 0
            end_index = len(index_data) - 1

        return start_index, end_index

    except Exception as e:
        print(f"Error processing index data: {e}")
        return 0, len(index_data) - 1

def strip_data(data: pd.Series, start_index: int, end_index: int):
    return data.loc[start_index:end_index]

def graph(data: pd.Series, index_data: pd.Series, channel_name: str, title: str, save=True):
    # Convert the index data (timestamps) from nanoseconds to human-readable datetime
    index_data = pd.to_datetime(index_data, unit='ns')

    # Set figure size for better visibility
    plt.figure(figsize=(12, 6))

    # Plot the data
    plt.plot(index_data, data, label=channel_name)

    # Label the axes
    plt.xlabel('Time', fontsize=14)
    plt.ylabel(channel_name, fontsize=14)

    # Add title and legend
    if not title:
        title = f"{channel_name} vs. Time"
    plt.title(title, fontsize=16)
    plt.legend()

    if save:
        # Save the plot as a PNG file
        plt.savefig(f"{output_dir}/{title}.png")
        plt.show()
    else:
        # Display the plot
        plt.show()

def main():
    if len(sys.argv) < 4:
        print("Usage: python grab_specific_data.py <channel> <index_channel> <start_timestamp> <end_timestamp> <title>")
        return

    channel = sys.argv[1]
    index_channel = sys.argv[2]
    start = int(sys.argv[3])
    end = int(sys.argv[4])
    if len(sys.argv) == 6:
        title = str(sys.argv[5])
    else:
        title = None

    # Read index channel and data channel
    index_data = read_in_channel(index_channel)  # Timestamps channel
    data = read_in_channel(channel)  # Data channel

    print(f"{len(data)} for data channel")
    print(f"{len(index_data)} for index channel")

    # print(f"Sample data from index channel (timestamps):\n{index_data.head()}")
    # print(f"Sample data from data channel:\n{data.head()}")

    # Find the start and end indices using index_data (timestamps)
    start_index, end_index = find_range(index_data, start, end)

    # Filter both index_data (timestamps) and data (values) using the found indices
    filtered_index_data = strip_data(index_data, start_index, end_index)
    filtered_data = strip_data(data, start_index, end_index)

    print(f"{len(filtered_data)} for filtered data channel")
    print(f"{len(filtered_index_data)} for filtered index channel")

    # Write the filtered data to CSV files
    write_csv(filtered_data, channel)
    write_csv(filtered_index_data, index_channel)

    # subtract 7 hours from each timestamp for pretty graphing
    filtered_index_data = filtered_index_data - 25200000000000

    # Graph the filtered data
    graph(filtered_data, filtered_index_data, channel, title)

if __name__ == "__main__":
    main()

"""
                        name            channel     index
    fuel mpv            gse_doa_24      65721       65540
    ox mpv              gse_doa_6       65699       65540
    igniter             gse_doa_25      65756       65540
    fuel prevalve       gse_doa_22      65715       65540
    ox prevalve         gse_doa_21      65714       65540
    fuel pt 1           gse_ai_3        65544       65538
    fuel pt 2           gse_ai_4        65545       65538
    fuel pt 3           gse_ai_35       65576       65538
    ox pt 1             gse_ai_6        65547       65538
    ox pt 2             gse_ai_7        65548       65538
    ox pt 3             gse_ai_8        65549       65538
    chamber pt 1        gse_ai_19       65560       65538
    chamber pt 2        gse_ai_28       65569       65538
    chamber pt 3        gse_ai_29       65570       65538
    chamber upper tc    gse_ai_77       65618       65538
    chamber lower tc    gse_ai_72       65613       65538

    upper bound             1715760000000000000
    loss of telemetry       1715756881666610043
    10 seconds before       1715756871000610043
    1 minute before         1715756821000610043
    5 minutes before        1715756581000610043
    1 hour before           1715753281000610043
    8 hours before          1715728081000610043
"""