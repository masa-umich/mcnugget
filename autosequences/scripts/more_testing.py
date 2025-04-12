import synnax
import time
import random

client = synnax.Synnax()

with client.open_streamer(["can_we_data", "gse_data_time"]) as streamer:
    while True:
        frame = streamer.read(0.01)
        if frame is None:
            continue
        data = frame["can_we_data"][-1]
        data_time = frame["gse_data_time"][-1]
        print(data)
        print(data_time)