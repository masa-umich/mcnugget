"""
    1. Specify channel to graph and its index channel
    2. Specify start and end indices for the data to graph
    3. Run the script
        - read in index channel data
        - read in specified channel data
        - find start/end indices using index channel data
        - filter specified channel data using start/end indices
        - write filtered data to CSV for both
        - generate graph
"""

import pandas as pd
import numpy as np
import json
import os
import sys

keys = json.load(open("key_mappings.json"))
data_dir = "/Users/evanhekman/masa/var/lib/docker/volumes/deploy_synnax-data/_data/cesium"
output_dir = "output_data"

def read_in_channel(channel_key: str, sample_count: int=1620000):
    meta = json.load(open(os.path.join(data_dir, f"{channel_key}/meta.json")))
    data_type_ = meta["data_type"]
    if data_type_ == "float32":
        data_type = np.float32
    elif data_type_ == "uint8":
        data_type = np.uint8
    elif data_type_ == "timestamp":
        data_type = np.uint64
    else:
        raise ValueError(f"Unknown data type: {data_type_}")
    
    print(f"processing {channel_key} as {data_type}")
    filepath = os.path.join(data_dir, f"{channel_key}/1.domain")
    try:
        data = np.fromfile(filepath, dtype=data_type)
        
        if data.size < sample_count:
            print(f"File {filepath} contains less than {sample_count} samples.")
            data_to_save = data
        else:
            data_to_save = data[-sample_count:]

        df = pd.DataFrame(data_to_save)

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return df

def write_csv(data: pd.DataFrame, channel_key: str):
    output_filepath = os.path.join(output_dir, f"{channel_key}.csv")
    data.to_csv(output_filepath, index=False)
    print(f"Data written to {output_filepath}")

def find_range(data: pd.DataFrame, start: int, end: int):
    # finds the first index with value >= start and the last index with value <= end
    start_index = data[data >= start].index[0]
    end_index = data[data <= end].index[-1]
    return start_index, end_index

def filter_data(data: pd.DataFrame, start: int, end: int):
    return data.loc[start:end]

def graph(data: pd.DataFrame, index_data: pd.DataFrame):
    import matplotlib.pyplot as plt
    plt.plot(index_data, data)
    plt.show()

def main():
    if (argc := len(sys.argv)) < 4:
        print("Usage: python grab_specific_data.py <channel> <index_channel> <start_timestamp> <end_timestamp>")
        return

    channel = sys.argv[1]
    index_channel = sys.argv[2]
    start = int(sys.argv[3])
    end = int(sys.argv[4])

    index_data = read_in_channel(index_channel)
    data = read_in_channel(channel)
    if len(index_data) != len(data):
        print(f"Before processing, index and data channels have different sizes: {index_data.size} vs {data.size}")
        return
    index_data = index_data.dropna()
    data = data.dropna()
    start_index, end_index = find_range(data, start, end)
    filtered_index_data = filter_data(index_data, start_index, end_index)
    filtered_data = filter_data(data, start_index, end_index)
    if len(filtered_index_data) != len(filtered_data):
        print(f"After processing, index and data channels have different sizes: {index_data.size} vs {data.size}")
        return
    write_csv(filtered_data, channel)
    write_csv(filtered_index_data, index_channel)

    graph(filtered_data, filtered_index_data)

if __name__ == "__main__":
    main()
