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

# Function to convert pressure from psig to Pa
def psig_to_pa(psig):
    return (psig + 14.7) * PSIG_TO_PA

# Function to calculate volumetric flowrate (Q) using the Venturi formula
def calculate_volumetric_flowrate(p1, p2, A1, A2, density):
    dp = p1 - p2
    Q = A2 * math.sqrt((2 * dp) / (density * ((A1 / A2) ** 2 - 1)))
    return Q


# Initialize REFPROP
refprop_path = "/Users/diegopeers/Desktop/REFPROP-cmake/build"
RP = REFPROPFunctionLibrary(refprop_path)
RP.SETPATHdll(refprop_path)
fluid = "OXYGEN"  # Update this if needed
units = RP.MASS_BASE_SI  
iMass = 1
iFlag = 0
z = [1.0]
RP.SETFLUIDSdll(fluid)

# Function to get oxidizer density from REFPROP
def get_ox_density(p1, t1):
    P_kPa = psig_to_pa(p1) / 1000
    T_K = t1 + 273.15

    # Call REFPROP function
    r = RP.REFPROPdll(fluid, "TP", "D", units, iMass, iFlag, T_K, P_kPa, z)

    if r.ierr != 0:
        print("REFPROP error:", r.herr)
        return None
    return r.Output[0]

# Initialize streamer for reading and writer for output
read_channels = [
    fuel_p1_channel,
    fuel_p2_channel,
    ox_p1_channel,
    ox_p2_channel,
    ox_t1_channel,
]
streamer = client.open_streamer(read_channels)

try:
    print("Starting flowmeter calculations...")
    while True:
        frame = streamer.read()
        if frame is None or not all(channel in frame for channel in read_channels):
            time.sleep(0.02)
            continue

        # Fuel flowrate calculation
        if fuel_p1_channel in frame and fuel_p2_channel in frame:
            fuel_p1 = psig_to_pa(frame[fuel_p1_channel][-1])
            fuel_p2 = psig_to_pa(frame[fuel_p2_channel][-1])
            Q_fuel = calculate_volumetric_flowrate(
                fuel_p1, fuel_p2, FUEL_INLET_AREA, FUEL_THROAT_AREA, FUEL_DENSITY
            )
            mdot_fuel = Q_fuel * FUEL_DENSITY

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
                print(f"Oxidizer mass flowrate: {mdot_ox:.3f} kg/s")
            else:
                print("Failed to retrieve oxidizer density from REFPROP.")

        time.sleep(0.02)

except KeyboardInterrupt:
    print("Terminating calculations...")
    streamer.close()
    client.close()
    print("Flowmeter calculations terminated.")
    exit()
