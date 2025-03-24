import time
import random
import synnax as sy
import websockets
import math
import sys

args = sys.argv[1:]
_NOISE = "noise" in args
_NEW_CHANNELS = "new_channels" in args

try:
    client = sy.Synnax(
        host="localhost", 
        port=9090, 
        username="synnax", 
        password="seldon", 
        secure=False
    )
except:
    print("unable to connect to cluster - is it running?")
    exit(0)

GSE_TIME = "gse_time"
RATE = (sy.Rate.HZ * 100).period.seconds

VALVES = {
    "GOX_MPV": 18,
    "METHANE_MPV": 16,
    "SPARK": 19,
}

PTS = {
    "TORCH_1": 31,
    "TORCH_2": 32,
    "TORCH_3": 33,
}

LOCAL = {}
REMOTE = {}
STATE = {}

for channel, index in VALVES.items():
    LOCAL[f"gse_state_{index}"] = 0
    REMOTE[f"gse_vlv_{index}"] = 0

for channel, index in PTS.items():
    LOCAL[f"gse_pt_{index}"] = 0

if _NEW_CHANNELS:
    gse_time = client.channels.create(
        name=GSE_TIME, 
        data_type=sy.DataType.TIMESTAMP,
        is_index=True, 
        retrieve_if_name_exists=True
    )
    print("creating channel gse_time")

    for channel in LOCAL.keys():
        print(f"creating channel {channel}")
        client.channels.create(
            name=channel,
            data_type=sy.DataType.UINT8 if "state" in channel else sy.DataType.FLOAT32,
            index=gse_time.key,
            retrieve_if_name_exists=True
        )

    for channel in REMOTE.keys():
        print(f"creating channel {channel}")
        client.channels.create(
            name=channel,
            data_type=sy.DataType.UINT8,
            virtual=True,
            retrieve_if_name_exists=True
        )

    client.channels.create(
        name="ignition_true",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        index=gse_time.key
    )

try:
    chan = GSE_TIME
    client.channels.retrieve(GSE_TIME)
    client.channels.retrieve("ignition_true")
    for channel in LOCAL.keys():
        chan = channel
        client.channels.retrieve(channel)
    for channel in REMOTE.keys():
        chan = channel
        client.channels.retrieve(channel)
    print(f"retrieved all channels")
except sy.exceptions.NotFoundError:
    print(f"error: could not retrieve channel {chan} - if running on a fresh cluster, please specify the `new_channels` argument")
    exit(0)

errors = 0
iteration = 0

STATE["torch_pressure"] = 0
STATE["ignition_true"] = 0
STATE["last_ignition"] = None

REMOTE[f"gse_vlv_{VALVES['GOX_MPV']}"] = 1
REMOTE[f"gse_vlv_{VALVES['METHANE_MPV']}"] = 1

print(f"reading from {len(list(REMOTE.keys()))} channels")
print(f"writing to {len(list(LOCAL.keys())) + 1} channels")
print(f"rate: {RATE} seconds")
with client.open_streamer(list(REMOTE.keys())) as streamer:
    with client.open_writer(
        sy.TimeStamp.now(),
        channels=list(LOCAL.keys()) + [GSE_TIME, "ignition_true"],
        name="torch_sim",
        enable_auto_commit=True,
    ) as writer:
        while True:
            try:
                time.sleep(RATE)
                while True:
                    f = streamer.read(0)
                    if f is None:
                        break
                    for c in f.channels:
                        REMOTE[c] = int(f[c][-1])
            
                for channel, state in REMOTE.items():
                    LOCAL[channel.replace("vlv", "state")] = state

                LOCAL["ignition_true"] = 0
                # if both valves + spark are open, maybe ignite
                if LOCAL[f"gse_state_{VALVES['GOX_MPV']}"] == 1 \
                    and LOCAL[f"gse_state_{VALVES['METHANE_MPV']}"] == 1 \
                    and LOCAL[f"gse_state_{VALVES['SPARK']}"] == 1:

                    if random.random() < 0.2:
                        STATE["torch_pressure"] = 200
                        LOCAL["ignition_true"] = 1
                        STATE["last_ignition"] = time.time()

                if STATE["last_ignition"] is not None:
                    diff = time.time() - STATE["last_ignition"]
                    STATE["torch_pressure"] -= diff ** 2 * 0.1
                    STATE["torch_pressure"] = max(0, STATE["torch_pressure"])

                # put values into LOCAL
                LOCAL[f"gse_pt_{PTS['TORCH_1']}"] = STATE["torch_pressure"]
                LOCAL[f"gse_pt_{PTS['TORCH_2']}"] = STATE["torch_pressure"]
                LOCAL[f"gse_pt_{PTS['TORCH_3']}"] = STATE["torch_pressure"]

                if _NOISE:
                    for pt in PTS.values():
                        LOCAL[f"gse_pt_{pt}"] = random.normalvariate(LOCAL[f"gse_pt_{pt}"], 15)
                
                LOCAL[GSE_TIME] = sy.TimeStamp.now()
                writer.write(LOCAL)
                
                if iteration % 6000 == 0:
                    print("iteration ", iteration)
                iteration += 1

            except KeyboardInterrupt:
                print("\nterminating sim")
                break

            # except Exception as e:
            #     print(f"error: {e}")
            #     errors += 1
            #     if errors >= 5:
            #         print("allowable errors exceeded, terminating sim")
            #         break
            #     continue

            except websockets.exceptions.ConnectionClosedError:
                print("lost connection to cluster, terminating sim")
                break
        