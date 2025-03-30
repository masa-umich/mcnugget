import time
import synnax
import math
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import os

# Initialize a connection to the Synnax server
client = synnax.Synnax()
RATE = (synnax.Rate.HZ * 100).period.seconds

# Constants
PSIG_TO_PA = 6894.76
FUEL_DENSITY = 800

# Flowmeter properties
OX_INLET_AREA = 0.00036868
OX_THROAT_AREA = 0.00013701
FUEL_INLET_AREA = 0.00019490
FUEL_THROAT_AREA = 0.00008128

# Channels for reading pressure and temperature data
fuel_p1_channel = "gse_pt_28_avg"
fuel_p2_channel = "gse_pt_13_avg"
ox_p1_channel = "gse_pt_9_avg"
ox_p2_channel = "gse_pt_10_avg"
ox_t1_channel = "gse_tc_5"

flowmeter_time = client.channels.create(
    name="flowmeter_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="fuel_mdot",
    data_type=synnax.DataType.FLOAT32,
    index=flowmeter_time.key,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="ox_mdot",
    data_type=synnax.DataType.FLOAT32,
    index=flowmeter_time.key,
    retrieve_if_name_exists=True,
)

# Function to convert pressure from psig to Pa
def psig_to_pa(psig):
    return (psig + 14.7) * PSIG_TO_PA

# Function to calculate volumetric flowrate (Q) using the Venturi formula
def calculate_volumetric_flowrate(p1, p2, A1, A2, density):
    # dp = p1 - p2
    # Q = A2 * math.sqrt((2 * dp) / (density * ((A1 / A2) ** 2 - 1)))
    Q = A1 * math.sqrt(
        (2 * (p1 - p2)) / (density * ((A1 / A2) ** 2 - 1))
    )
    return Q

# Initialize REFPROP
refprop_path = os.environ.get("RPPREFIX")
RP = REFPROPFunctionLibrary(refprop_path)
RP.SETPATHdll(refprop_path)
fluid = "NITROGEN"  # Update this if needed, i.e. OXYGEN
units = RP.MASS_BASE_SI
iMass = 1
iFlag = 0
z = [1.0]
RP.SETFLUIDSdll(fluid)

# Function to get oxidizer density from REFPROP
def get_ox_density(p1, t1):
    """
    pressure in psi and temperature in celsius
    """
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
    "gse_ai_time"
]
WRITE_DATA = {}
STATE = {}

def test() -> bool:
    print("psig_to_pa")
    if abs(psig_to_pa(0) - 101352) > 1:
        print("expected: 101352")
        print("actual: ", psig_to_pa(0))
        return False
    else:
        print("psig_to_pa function passed")

    # 50 psi difference means 344738 Pa difference
    print("\ncalculate_volumetric_flowrate")
    ox_density = 806
    ox_Q = calculate_volumetric_flowrate(
        psig_to_pa(50),
        psig_to_pa(0),
        OX_INLET_AREA,
        OX_THROAT_AREA,
        ox_density,
    )
    ox_mdot = ox_density * ox_Q
    print("expected: 3.4791")
    print("actual: ", ox_mdot)
    if abs(ox_mdot - 3.4791) > 0.1:
        return False
    
    print("\nrefprop test")
    # Inputs
    t_celsius = -183
    p_psig = 0
    fluid = 'OXYGEN.FLD'   # From REFPROP's fluids folder [3][8]
    T_K = t_celsius + 273.15
    P_kPa = (p_psig + 14.7) * 6.89476  # Convert psig → kPa (absolute)
    z = [1.0]  # Pure oxygen composition

    # REFPROP parameters
    inputs = "TP"          # Input mode: Temperature (K) & Pressure (kPa)
    outputs = "D"          # Output: Density (kg/m³)
    units = 21             # SI units: kg, kPa, K [3]
    iMass = 1              # Mass-based output (kg/m³)
    iFlag = 1              # Force liquid phase [3]

    # Call REFPROP
    r = RP.REFPROPdll(fluid, inputs, outputs, units, iMass, iFlag, T_K, P_kPa, z)
    print("expected: 1141.0")
    print("actual: ", r.Output[0])
    if r.Output[0] - 1141 > 1:
        return False

    print("\nox density")
    ox_density = get_ox_density(1.81, -210)
    print("expected: 867.2")
    print("actual: ", ox_density)
    if abs(ox_density - 867.2) > 0.1:
        return False

t = test()
if not t:
    print("Test failed :(")
    # exit(1)
if t:
    print("Test passed!")
    # exit(1)

# with client.open_streamer(read_channels) as imitation_streamer:
with client.control.acquire("flowmeter cals", read_channels, [], 3) as imitation_streamer:
    with client.open_writer(synnax.TimeStamp.now(), ["fuel_mdot", "ox_mdot", "flowmeter_time"], 20, enable_auto_commit=True) as writer:
        print("Starting flowmeter calculations...")
        time.sleep(1)
        errors = 0
        iteration = 0
        while True:
            try:
                for chan in read_channels:
                    STATE[chan] = imitation_streamer[chan]

                # Fuel flowrate calculation
                try:
                    fuel_p1 = psig_to_pa(max(STATE[fuel_p1_channel], 0))
                    fuel_p2 = psig_to_pa(max(STATE[fuel_p2_channel], 0))
                    Q_fuel = calculate_volumetric_flowrate(
                        fuel_p1, fuel_p2, FUEL_INLET_AREA, FUEL_THROAT_AREA, FUEL_DENSITY
                    )
                    mdot_fuel = Q_fuel * FUEL_DENSITY

                    WRITE_DATA["fuel_mdot"] = mdot_fuel
                except ValueError as e:
                    WRITE_DATA["fuel_mdot"] = -1

                # Oxidizer flowrate calculation
                try:
                    ox_p1 = psig_to_pa(max(STATE[ox_p1_channel], 0))
                    ox_p2 = psig_to_pa(max(STATE[ox_p2_channel], 0))
                    ox_temp = STATE[ox_t1_channel] + 273.15

                    ox_density = get_ox_density(ox_p1, ox_temp)
                    if ox_density is not None:
                        Q_ox = calculate_volumetric_flowrate(
                            ox_p1, ox_p2, OX_INLET_AREA, OX_THROAT_AREA, ox_density
                        )
                        mdot_ox = Q_ox * ox_density
                        WRITE_DATA["ox_mdot"] = mdot_ox
                    else:
                        raise Exception("Failed to retrieve oxidizer density from REFPROP.")
                except ValueError as e:
                    WRITE_DATA["ox_mdot"] = -1

                if iteration % 6000 == 0:
                    print("iteration ", iteration)
                iteration += 1

                WRITE_DATA["flowmeter_time"] = STATE["gse_ai_time"]

                writer.write(WRITE_DATA)
                time.sleep(RATE)

            except KeyboardInterrupt:
                print("Terminating calculations...")
                print("Flowmeter calculations terminated.")
                exit(0)