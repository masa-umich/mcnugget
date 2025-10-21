import time
import synnax
import statistics
import synnax.control
from collections import deque

client = synnax.Synnax(
    host="141.212.192.160",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False,
)
channels_to_average = []

index = client.channels.create(
    name="gse_avaverage_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

client.channels.create(
    name="fuel_tanks",
    data_type=synnax.DataType.FLOAT32,
    index=index.key,
    retrieve_if_name_exists=True
)
client.channels.create(
    name="ox_tanks",
    data_type=synnax.DataType.FLOAT32,
    index=index.key,
    retrieve_if_name_exists=True
)


READ = ["gse_pt_19_avg", "gse_pt_20_avg", "gse_pt_21_avg", "gse_pt_39_avg", "gse_pt_40_avg", "gse_pt_41_avg", "gse_average_time"]
WRITE = ["fuel_tanks", "ox_tanks", "gse_avaverage_time"]

RATE = (synnax.Rate.HZ * 200).period.seconds

with client.open_streamer(READ) as streamer:
    initial_frame = streamer.read(1)
    if initial_frame is None:
        print("unable to stream data")
        exit(1)
    starting_time = initial_frame["gse_average_time"][-1]
    with client.open_writer(starting_time, WRITE, 20, enable_auto_commit=True) as writer:
        time.sleep(1)
        iteration = 0
        while True:
            try:
                frame = streamer.read(0.0025)
                if frame is None:
                    continue
                WRITE_DATA = {
                    "fuel_tanks": statistics.median([frame["gse_pt_19_avg"][-1], frame["gse_pt_20_avg"][-1], frame["gse_pt_21_avg"][-1]]),
                    "ox_tanks": statistics.median([frame["gse_pt_39_avg"][-1], frame["gse_pt_40_avg"][-1], frame["gse_pt_41_avg"][-1]]),
                    "gse_avaverage_time": frame["gse_average_time"][-1]
                }
                writer.write(WRITE_DATA)

            except KeyboardInterrupt:
                print("terminating script...")
                break

            finally:
                if iteration % 6000 == 0:
                    print("iteration ", iteration)
                iteration += 1
