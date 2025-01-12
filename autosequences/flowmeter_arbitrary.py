import time
import synnax
import math


# Mock Synnax connection setup
class MockSynnaxClient:
    def open_streamer(self, channels):
        return MockStreamer()

    def open_writer(self, timestamp, channels, name, enable_auto_commit):
        return MockWriter()

    class channels:
        @staticmethod
        def create(name, data_type, retrieve_if_name_exists):
            print(f"Channel {name} created with data type {data_type}")
            return MockChannel(name)


class MockStreamer:
    def read(self, delay):
        # Mocked frame data simulating sensor readings
        frame = {
            "fuel_inlet_PT": [100],  # psig
            "fuel_throat_PT": [90],  # psig
            "ox_inlet_PT": [120],  # psig
            "ox_throat_PT": [100],  # psig
            "ox_inlet_TC": [20],  # Celsius
        }
        return frame


class MockWriter:
    def write(self, data):
        print("\nData written:", data)

    def close(self):
        print("Writer closed.")


class MockChannel:
    def __init__(self, name):
        self.name = name


# Replace synnax.Synnax with the MockSynnaxClient for testing
synnax.Synnax = MockSynnaxClient

# Constants
PSIG_TO_PA = 6894.76
FUEL_DENSITY = 800  # kg/m³

# Flowmeter properties
OX_INLET_AREA = 0.00036868
OX_THROAT_AREA = 0.00013701
FUEL_INLET_AREA = 0.00019490
FUEL_THROAT_AREA = 0.00008128

# Channels for reading pressure and temperature data
fuel_p1_channel = "fuel_inlet_PT"
fuel_p2_channel = "fuel_throat_PT"
ox_p1_channel = "ox_inlet_PT"
ox_p2_channel = "ox_throat_PT"
ox_t1_channel = "ox_inlet_TC"  # For ox density calculation using REFPROP

# Output channels
fuel_mdot_channel = "fuel_mdot"
ox_mdot_channel = "ox_mdot"

# Set a realistic rate for testing
rate = 0.2
print("rate:", rate)


# Function to convert pressure from psig to pa
def psig_to_pa(psig):
    return (psig + 14.7) * PSIG_TO_PA


# Function to calculate volumetric flowrate (Q) using Venturi formula
def calculate_volumetric_flowrate(p1, p2, A1, A2, density):
    dp = p1 - p2
    Q = A2 * math.sqrt((2 * dp) / (density * ((A1 / A2) ** 2 - 1)))
    return Q


# Placeholder function for ox density from REFPROP (to be implemented)
def get_ox_density(p1, t1):
    return 1141.0  # Placeholder value


# Setting up channels in Synnax
client = synnax.Synnax()
fuel_mdot = client.channels.create(
    name=fuel_mdot_channel,
    data_type="FLOAT64",
    retrieve_if_name_exists=True,
)
ox_mdot = client.channels.create(
    name=ox_mdot_channel,
    data_type="FLOAT64",
    retrieve_if_name_exists=True,
)
print("Created/retrieved mass flowrate channels for fuel and oxidizer.")

# Initialize streamer for reading and writer for output
streamer = client.open_streamer(
    [fuel_p1_channel, fuel_p2_channel, ox_p1_channel, ox_p2_channel, ox_t1_channel]
)
writer = client.open_writer(
    "now",
    [fuel_mdot_channel, ox_mdot_channel],
    name="flowmeter_autosequence.py",
    enable_auto_commit=True,
)

# Counter for stopping after 10 values
counter = 0
max_iterations = 10

try:
    print("Starting flowmeter calculations...")
    time.sleep(1)
    while counter < max_iterations:
        frame = streamer.read(0)
        if frame is None:
            time.sleep(rate)
            continue

        # Fuel flowrate calculation
        fuel_p1 = psig_to_pa(frame[fuel_p1_channel][-1])
        fuel_p2 = psig_to_pa(frame[fuel_p2_channel][-1])
        Q_fuel = calculate_volumetric_flowrate(
            fuel_p1, fuel_p2, FUEL_INLET_AREA, FUEL_THROAT_AREA, FUEL_DENSITY
        )
        mdot_fuel = Q_fuel * FUEL_DENSITY
        writer.write({fuel_mdot_channel: mdot_fuel})
        print(f"Fuel mass flowrate: {mdot_fuel:.3f} kg/s")

        # Oxidizer flowrate calculation
        ox_p1 = psig_to_pa(frame[ox_p1_channel][-1])
        ox_p2 = psig_to_pa(frame[ox_p2_channel][-1])
        ox_temp = frame[ox_t1_channel][-1] + 273.15

        ox_density = get_ox_density(ox_p1, ox_temp)
        Q_ox = calculate_volumetric_flowrate(
            ox_p1, ox_p2, OX_INLET_AREA, OX_THROAT_AREA, ox_density
        )
        mdot_ox = Q_ox * ox_density
        writer.write({ox_mdot_channel: mdot_ox})
        print(f"Oxidizer mass flowrate: {mdot_ox:.3f} kg/s")

        counter += 1
        time.sleep(rate)

except KeyboardInterrupt:
    print("Terminating calculations...")

finally:
    writer.close()
    streamer.close()
    print("Flowmeter calculations terminated.")
