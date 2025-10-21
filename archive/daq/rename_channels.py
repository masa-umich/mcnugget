import json
import synnax
import pathlib

client = synnax.Synnax()
json_path = pathlib.Path("__file__").parent / "config" / "channels.json"
with open(json_path, "r") as f:
    data = json.load(f)
    for new_channel, old_channel in data.items():
        client.channels.rename(old_channel, new_channel)
        print(f"Renamed {old_channel} to {new_channel}")