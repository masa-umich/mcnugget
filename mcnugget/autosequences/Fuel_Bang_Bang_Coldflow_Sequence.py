""""
Autosequence name: Fuel Bang Bang Coldflow Sequence

Autosequence high level description:
- Controlling fuel tank pressure using a bang bang control system
- Fuel TPC 1 and Fuel TPC 2 will be used for this TPC test
    - These valves will not be the 1-24 channels (most likely 25/26)
- Fuel prevalve will be used in place of MPVs

Autosequence detailed description:
- Initial system state: fuel tank pressure at target tank pressure
- Abort: close prevavles and open fuel vent and ox low flow vent
- Monitor tank pressures from fuel PT1, PT2, PT3 via averaging / sensor voting

Autosequence Steps:
1. Close vents 
"""
import time
import synnax as sy
from synnax.control.controller import Controller
import syauto
import statistics

PRESS_STEP_DELAY = (1 * sy.TimeSpan.SECOND).seconds  # Seconds

#connecting to local simulation server
client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

#connecting to MASA Remote for testing
# client = sy.Synnax(
#     host="synnax.masa.engin.umich.edu",
#     port=80,
#     username="synnax",
#     password="seldon",
#     secure=True
# )

#Valves autosequence will control
FUEL_TPC_1_CMD = "gse_doc_25"
FUEL_TPC_1_ACK = "gse_doa_25"
FUEL_TPC_2_CMD = "gse_doc_26"
FUEL_TPC_2_ACK = "gse_doa_26"
FUEL_PREVALVE_CMD = "gse_doc_22"
FUEL_PREVALVE_ACK = "gse_doa_22"
FUEL_VENT_CMD = "gse_doc_15"
FUEL_VENT_ACK = "gse_doa_15"
OX_LOW_FLOW_VENT_CMD = "gse_doc_16"
OX_LOW_FLOW_VENT_ACK = "gse_doa_16"
FUEL_PRE_PRESS_VALVE_CMD = "gse_doc_11"
FUEL_PRE_PRESS_VALVE_ACK = "gse_doa_11"

#PTs and sensor readings autosequence will control
FUEL_TANK_PT_1 = "gse_ai_1"
FUEL_TANK_PT_2 = "gse_ai_2"
FUEL_TANK_PT_3 = "gse_ai_3"

WRITE_TO = []
READ_FROM = []

for i in range(1, 27):
    WRITE_TO.append(f"gse_doc_{i}")
    READ_FROM.append(f"gse_doa_{i}")

for i in range(1, 37):
    READ_FROM.append(f"gse_ai_{i}")
for i in range(69, 73):
    READ_FROM.append(f"gse_ai_{i}")
READ_FROM.append("daq_time")

print(WRITE_TO)

print()

print(READ_FROM)

#Change these based on testing requirements
TPC_STEP = 2
TARGET_1 = 4000
BOUND_1 = TARGET_1 - TPC_STEP
TARGET_2 = BOUND_1 - TPC_STEP
BOUND_2 = TARGET_2 - TPC_STEP

MAXIMUM = TARGET_1 + 20
MINIMUM = BOUND_2 - 20

# this initializes a connection to the client with access to all the needed channels
with client.control.acquire(name="bang_bang_tpc", write=WRITE_TO, read=READ_FROM, write_authorities=252) as auto:
    print(auto["gse_doa_9"])
    fuel_tpc_1 = syauto.Valve(auto=auto, cmd=FUEL_TPC_1_CMD, ack=FUEL_TPC_1_ACK, normally_open=False)
    fuel_tpc_2 = syauto.Valve(auto=auto, cmd=FUEL_TPC_2_CMD, ack=FUEL_TPC_2_ACK, normally_open=False)
    fuel_prevalve = syauto.Valve(auto=auto, cmd=FUEL_PREVALVE_CMD, ack=FUEL_PREVALVE_ACK, normally_open=False)
    fuel_pre_press = syauto.Valve(auto=auto, cmd=FUEL_PRE_PRESS_VALVE_CMD, ack=FUEL_PRE_PRESS_VALVE_ACK, normally_open=False)

    fuel_vent = syauto.Valve(auto=auto, cmd=FUEL_VENT_CMD, ack=FUEL_VENT_ACK, normally_open=True)
    ox_low_flow_vent = syauto.Valve(auto=auto, cmd=OX_LOW_FLOW_VENT_CMD, ack=OX_LOW_FLOW_VENT_ACK, normally_open=True)

    def run_tpc():
        fuel_tank_pressures = 2000  # arbitrary
        if auto[FUEL_TANK_PT_1] or auto[FUEL_TANK_PT_1] or auto[FUEL_TANK_PT_1]:
            fuel_tank_pressures = statistics.median(auto[PT] for PT in [FUEL_TANK_PT_1, FUEL_TANK_PT_2, FUEL_TANK_PT_3])
        fuel_tpc_1_open = auto[FUEL_TPC_1_ACK]
        fuel_tpc_2_open = auto[FUEL_TPC_2_ACK]

        """
            * both TPCs close if pressure rises above TARGET_1
        TARGET_1
        BOUND_1
            * TPC 1 opens if pressure falls below BOUND_1
            * TPC 2 closes if pressure rises above TARGET_2
        TARGET_2
        BOUND_2
            * both TPCs open if pressure falls below BOUND_2

        This leaves us with 4 distinct states, each tied to the direction the 
        pressure is going as well as the targets/bounds it exceeds/falls below.

        To handle these states we actually only need 3 checks

        TARGET_1 < pressure
            * both TPCs closed

        TARGET_2 < pressure < BOUND_1
            * TPC 1 open, TPC 2 closed

        pressure < BOUND_2
            * both TPCs open

        Otherwise, we leave the system alone.
        """

        # aborts if the pressure is above the accepted maximum
        if fuel_tank_pressures > MAXIMUM:
            # abort
            print("pressure has exceeded acceptable range - ABORTING")
            syauto.close_all(auto, [fuel_tpc_1, fuel_tpc_2])
            print ("TPC 1: CLOSED | TPC 2: CLOSED")
            return

        elif fuel_tank_pressures > TARGET_1:
            # both valves closed
            if fuel_tpc_1_open or fuel_tpc_2_open:
                print(f"pressure above {TARGET_1}")
                syauto.close_all(auto, [fuel_tpc_1, fuel_tpc_2])
                print ("TPC 1: CLOSED | TPC 2: CLOSED")

        elif TARGET_2 < fuel_tank_pressures and fuel_tank_pressures < BOUND_1:
            # valve 1 open, valve 2 closed
            if not fuel_tpc_1_open or fuel_tpc_2_open:
                print(f"pressure between {TARGET_2} and {BOUND_1}")
                syauto.open_close_many_valves(auto, [fuel_tpc_1], [fuel_tpc_2])
                print("TPC 1: OPEN | TPC 2: CLOSED")

        elif fuel_tank_pressures < BOUND_2:
            # both valves open
            if not fuel_tpc_1_open or not fuel_tpc_2_open:
                print(f"pressure below {BOUND_2}")
                syauto.open_all(auto, [fuel_tpc_1, fuel_tpc_2])
                print("TPC 1: OPEN | TPC 2: OPEN")

        # if the pressure drops below 15, the tanks are mostly empty and the test is finished
        if fuel_tank_pressures < 15:
            print("pressure below 15 - FINISHED")
            return

    try:
        start = sy.TimeStamp.now()

        print("Starting Fuel Bang Bang Coldflow Sequence. Setting initial system state.")
        # set initial system state
        syauto.close_all(auto, [fuel_vent, ox_low_flow_vent, fuel_tpc_1, fuel_tpc_2, fuel_prevalve, fuel_pre_press])
        print("All valves and vents closed. Beinning test")

        print("Opening Fuel Prevalve")
        fuel_prevalve.open()
        time.sleep(1)

        print("Initiating TPC")
        auto.wait_until(run_tpc())

        print("Test complete. Safing System")

        # Create a range in the autosequence
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Fuel Bang Bang Coldflow Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

        syauto.open_close_many_valves(auto, [ox_low_flow_vent, fuel_vent], [fuel_tpc_1, fuel_tpc_2, fuel_prevalve])
        input("press any key to terminate the autosequence")

    except KeyboardInterrupt:
        print("Test interrupted. Safing System")
        # close all prevalves and open all vents
        syauto.open_close_many_valves(auto, [ox_low_flow_vent, fuel_vent], [fuel_tpc_1, fuel_tpc_2, fuel_prevalve])
        input("press any key to terminate the autosequence")
