import synnax
import json

keys = {}

def find_channels(client, channel_name_prefix, start, end):
    for i in range(start, end + 1):
        channel_name = f"{channel_name_prefix}_{i}"
        try:
            # Attempt to retrieve the channel by its name
            channel = client.channels.retrieve(channel_name)
            print(f"Found channel: {channel_name} - Key: {channel.key}")
            keys[channel_name] = channel.key
        except Exception as e:
            print(f"Channel {channel_name} not found.")

def main():
    # Connect to the Synnax server
    client = synnax.Synnax(
        host="141.212.192.160",
        port=80,
        username="synnax",
        password="seldon"
    )

    # Search for 'gse_ai_1' through 'gse_ai_76'
    find_channels(client, "gse_ai", 1, 76)

    # Search for 'gse_doa_1' through 'gse_doa_25'
    find_channels(client, "gse_doa", 1, 25)
    
    print(keys)

    with open("key_mappings.json", "w") as f:
        json.dump(keys, f)

if __name__ == "__main__":
    main()
