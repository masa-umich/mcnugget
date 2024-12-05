import synnax
import json
import time
import os

client = synnax.Synnax()

ambient = {}
channels_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "channels.json")
ambient_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "ambient.json")
with open(channels_path, 'r') as f:
    channels = json.load(f)
    channels = [c for c in channels.keys() if "pt" in c]
    with client.control.acquire(name="ambientization", read=channels, write=None) as auto:
        time.sleep(1)
        for channel in channels:
            ambient[channel] = float(auto[channel])
            print(f"{channel}: {ambient[channel]}")

with open(ambient_path, 'w') as f:
    json.dump(ambient, f, indent=4)
