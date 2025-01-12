import time
import synnax
import math
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary

# Initialize a connection to the Synnax server
client = synnax.Synnax()

# Constants
PSIG_TO_PA = 6894.76
FUEL_DENSITY = 800

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
ox_t1_channel = "ox_inlet_TC"

# Output channels
fuel_mdot_channel = "fuel_mdot"
ox_mdot_channel = "ox_mdot"

# Synnax rate
rate = (synnax.Rate.HZ * 50).period.seconds
print("rate: ", rate)


# Function to convert pressure from psig to Pa
def psig_to_pa(psig):
    return (psig + 14.7) * PSIG_TO_PA


# Function to calculate volumetric flowrate (Q) using the Venturi formula
def calculate_volumetric_flowrate(p1, p2, A1, A2, density):
    dp = p1 - p2
    Q = A2 * math.sqrt((2 * dp) / (density * ((A1 / A2) ** 2 - 1)))
    return Q


# Initialize REFPROP
refprop_path = "/Users/diegopeers/Desktop/REFPROP-cmake/build/librefprop.dylib"
RP = REFPROPFunctionLibrary(refprop_path)
RP.SETPATHdll(refprop_path)
fluid = "OXYGEN"  # Update this if needed
units = RP.MASS_BASE_SI  # Units code for SI units with mass base
iMass = 1
iFlag = 0
z = [1.0]
RP.SETFLUIDSdll(fluid)
# RP.SETUNITSdll(units)


# Function to get oxidizer density from REFPROP
def get_ox_density(p1, t1):
    P_kPa = p1 / 1000
    T_K = t1  # Already in K

    # Call REFPROP function
    r = RP.REFPROPdll(fluid, "TP", "D", units, iMass, iFlag, T_K, P_kPa, z)

    if r.ierr != 0:
        print("REFPROP error:", r.herr)
        return None
    else:
        density = r.Output[0]
        return density


flowmeter_time = client.channels.create(
    name="flowmeter_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

# Setting up channels in Synnax
fuel_mdot = client.channels.create(
    name=fuel_mdot_channel,
    data_type=synnax.DataType.FLOAT64,
    retrieve_if_name_exists=True,
    index=flowmeter_time.key,
)
ox_mdot = client.channels.create(
    name=ox_mdot_channel,
    data_type=synnax.DataType.FLOAT64,
    retrieve_if_name_exists=True,
    index=flowmeter_time.key,
)
print("Created/retrieved mass flowrate channels for fuel and oxidizer.")

# Initialize streamer for reading and writer for output
read_channels = [
    fuel_p1_channel,
    fuel_p2_channel,
    ox_p1_channel,
    ox_p2_channel,
    ox_t1_channel,
]
write_channels = [fuel_mdot_channel, ox_mdot_channel]
streamer = client.open_streamer(read_channels)
writer = client.open_writer(
    synnax.TimeStamp.now(),
    channels=write_channels,
    name="flowmeter.py",
    enable_auto_commit=True,
)

try:
    print("Starting flowmeter calculations...")
    time.sleep(1)
    while True:
        frame = streamer.read(0)
        if frame is None:
            time.sleep(rate)
            continue

        dictionary = {
            "flowmeter_time": synnax.TimeStamp.now(),
        }
        # Fuel flowrate calculation
        if fuel_p1_channel in frame and fuel_p2_channel in frame:
            fuel_p1 = psig_to_pa(frame[fuel_p1_channel][-1])
            fuel_p2 = psig_to_pa(frame[fuel_p2_channel][-1])
            Q_fuel = calculate_volumetric_flowrate(
                fuel_p1, fuel_p2, FUEL_INLET_AREA, FUEL_THROAT_AREA, FUEL_DENSITY
            )
            mdot_fuel = Q_fuel * FUEL_DENSITY

            # finish the dictionary
            dictionary = {
                "fuel_mdot": hththehth,
                "ox_mdot": ox,
                "flowmeter_time": synnax.TimeStamp.now(),
            }

            writer.write(
                {fuel_mdot_channel: mdot_fuel, flowmeter_time: synnax.TimeStamp.now()}
            )
            print(f"Fuel mass flowrate: {mdot_fuel:.3f} kg/s")

        # Oxidizer flowrate calculation
        if ox_p1_channel in frame and ox_p2_channel in frame and ox_t1_channel in frame:
            ox_p1 = psig_to_pa(frame[ox_p1_channel][-1])
            ox_p2 = psig_to_pa(frame[ox_p2_channel][-1])
            ox_temp = frame[ox_t1_channel][-1] + 273.15

            ox_density = get_ox_density(ox_p1, ox_temp)
            if ox_density is not None:
                Q_ox = calculate_volumetric_flowrate(
                    ox_p1, ox_p2, OX_INLET_AREA, OX_THROAT_AREA, ox_density
                )
                mdot_ox = Q_ox * ox_density
                writer.write(
                    {ox_mdot_channel: mdot_ox, flowmeter_time: synnax.TimeStamp.now()}
                )
                print(f"Oxidizer mass flowrate: {mdot_ox:.3f} kg/s")
            else:
                print("Failed to retrieve oxidizer density from REFPROP.")

        time.sleep(rate)

except KeyboardInterrupt:
    print("Terminating calculations...")
    time.sleep(2)
    writer.close()
    streamer.close()
    client.close()
    print("Flowmeter calculations terminated.")
    exit()
