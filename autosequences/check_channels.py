from synnax import Synnax

# Connect to Synnax cluster
client = Synnax(host="localhost", port=9090)

# List of expected channels
channel_names = [
    "fuel_inlet_PT",
    "fuel_throat_PT",
    "ox_inlet_PT",
    "ox_throat_PT",
    "ox_inlet_TC",
]

# Check if channels exist
print("\nChecking for required Synnax channels...\n")
missing_channels = []

for name in channel_names:
    channel = client.channels.retrieve_by_name(name)
    if channel is None:
        print(f"❌ Channel NOT found: {name}")
        missing_channels.append(name)
    else:
        print(f"✅ Channel exists: {name} -> {channel.key}")

# Alert if any channels are missing
if missing_channels:
    print("\n⚠️ WARNING: Some required channels are missing in Synnax.")
    print("Run `flowmeter_sim.py` first to create them.")
else:
    print("\n✅ All required channels are present. You can run `flowmeter.py` safely.")
