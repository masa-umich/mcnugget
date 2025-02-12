import time
import synnax
import random

# Initialize a connection to the Synnax server
client = synnax.Synnax()

# Constants
PSIG_TO_PA = 6894.76

# Flowmeter properties (same as in flowmeter.py)
OX_INLET_AREA = 0.00036868
OX_THROAT_AREA = 0.00013701
FUEL_INLET_AREA = 0.00019490
FUEL_THROAT_AREA = 0.00008128

# Channel names for simulated pressure and temperature values
fuel_p1_channel = "fuel_inlet_PT"
fuel_p2_channel = "fuel_throat_PT"
ox_p1_channel = "ox_inlet_PT"
ox_p2_channel = "ox_throat_PT"
ox_t1_channel = "ox_inlet_TC"

# Creating Synnax channels for writing data
channels = {
    fuel_p1_channel: "Fuel Flowmeter Inlet Pressure",
    fuel_p2_channel: "Fuel Flowmeter Throat Pressure",
    ox_p1_channel: "Ox Flowmeter Inlet Pressure",
    ox_p2_channel: "Ox Flowmeter Throat Pressure",
    ox_t1_channel: "Ox Flowmeter Inlet Temperature",
}

# Create a timestamp channel for indexing
flowmeter_time = client.channels.create(
    name="flowmeter_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

# Create channels if they don't exist
for key in channels.keys():
    client.channels.create(
        name=key,
        data_type=synnax.DataType.FLOAT64,
        index=flowmeter_time.key,
        retrieve_if_name_exists=True,
    )

# Open a writer stream
writer = client.open_writer(
    synnax.TimeStamp.now(),
    channels=list(channels.keys()) + [flowmeter_time.key],
    name="flowmeter_sim.py",
    enable_auto_commit=True,
)


def generate_sensor_data():
    """Simulate pressure and temperature values and write them to Synnax."""
    try:
        while True:
            timestamp = synnax.TimeStamp.now()

            # Generate random values within a realistic range give in psig except for last one which is Celsius and the flowmeter.py script will convert to Kelvin.
            fuel_p1 = random.uniform(500, 600)
            fuel_p2 = random.uniform(400, 500)
            ox_p1 = random.uniform(700, 800)
            ox_p2 = random.uniform(600, 700)
            ox_t1 = random.uniform(-23, 27)

            # Write values to Synnax
            writer.write(
                {
                    fuel_p1_channel: fuel_p1,
                    fuel_p2_channel: fuel_p2,
                    ox_p1_channel: ox_p1,
                    ox_p2_channel: ox_p2,
                    ox_t1_channel: ox_t1,
                    "flowmeter_time": timestamp,
                }
            )

            # Print debug output
            print(f"Timestamp: {timestamp}")
            print(f"  Fuel: p1={fuel_p1:.2f} psig, p2={fuel_p2:.2f} psig")
            print(
                f"  Oxidizer: p1={ox_p1:.2f} psig, p2={ox_p2:.2f} psig, T1={ox_t1:.2f} Celsius"
            )

            time.sleep(0.02)  # 50 Hz update rate (same as flowmeter.py)

    except KeyboardInterrupt:
        print("Stopping flowmeter simulation...")
        writer.close()
        client.close()
        exit()


generate_sensor_data()
