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
OX_DRAIN_CMD = "gse_doc_14"
OX_DRAIN_ACK = "gse_doa_14"

#PTs and sensor readings autosequence will control
FUEL_TANK_PT_1 = "gse_ai_3"
FUEL_TANK_PT_2 = "gse_ai_4"
FUEL_TANK_PT_3 = "gse_ai_35"

FUEL_TANK_PT_1_VALS = []
FUEL_TANK_PT_2_VALS = []
FUEL_TANK_PT_3_VALS = []

RUNNING_MEDIAN_SIZE = 20

def get_medians(auto: Controller) -> sy.DataType.FLOAT32:
    FUEL_TANK_PT_1_VALS.append(auto[FUEL_TANK_PT_1])
    FUEL_TANK_PT_2_VALS.append(auto[FUEL_TANK_PT_2])
    FUEL_TANK_PT_3_VALS.append(auto[FUEL_TANK_PT_3])

    for pt in [FUEL_TANK_PT_1_VALS, FUEL_TANK_PT_2_VALS, FUEL_TANK_PT_3_VALS]:
        if len(pt) > RUNNING_MEDIAN_SIZE:
            pt.pop(0)

    return statistics.median([
        statistics.mean(FUEL_TANK_PT_1_VALS), 
        statistics.mean(FUEL_TANK_PT_2_VALS), 
        statistics.mean(FUEL_TANK_PT_3_VALS)])

WRITE_TO = []
READ_FROM = []

for i in range(1, 30):
    WRITE_TO.append(f"gse_doc_{i}")
    READ_FROM.append(f"gse_doa_{i}")

for i in range(1, 38):
    READ_FROM.append(f"gse_ai_{i}")
for i in range(69, 73):
    READ_FROM.append(f"gse_ai_{i}")

#Change these based on testing requirements
TARGET_1 = 460
TARGET_2 = 440
TARGET_3 = 420

MAXIMUM = 525
MINIMUM = 15

START_TPC = time.time()

# this initializes a connection to the client with access to all the needed channels
with client.control.acquire(name="bang_bang_tpc", write=WRITE_TO, read=READ_FROM, write_authorities=200) as auto:
    time.sleep(1)
    fuel_tpc_1 = syauto.Valve(auto=auto, cmd=FUEL_TPC_1_CMD, ack=FUEL_TPC_1_ACK, normally_open=False)
    fuel_tpc_2 = syauto.Valve(auto=auto, cmd=FUEL_TPC_2_CMD, ack=FUEL_TPC_2_ACK, normally_open=False)
    fuel_prevalve = syauto.Valve(auto=auto, cmd=FUEL_PREVALVE_CMD, ack=FUEL_PREVALVE_ACK, normally_open=False)
    fuel_pre_press = syauto.Valve(auto=auto, cmd=FUEL_PRE_PRESS_VALVE_CMD, ack=FUEL_PRE_PRESS_VALVE_ACK, normally_open=False)

    fuel_vent = syauto.Valve(auto=auto, cmd=FUEL_VENT_CMD, ack=FUEL_VENT_ACK, normally_open=True)
    ox_low_flow_vent = syauto.Valve(auto=auto, cmd=OX_LOW_FLOW_VENT_CMD, ack=OX_LOW_FLOW_VENT_ACK, normally_open=True)
    
    ox_drain = syauto.Valve(auto=auto, cmd=OX_DRAIN_CMD, ack=OX_DRAIN_ACK, normally_open=False)

    ox_press_iso = syauto.Valve(auto=auto, cmd="gse_doc_1", ack="gse_doa_1", normally_open=False)
    ox_dome_iso = syauto.Valve(auto=auto, cmd="gse_doc_5", ack="gse_doa_5", normally_open=False)
    ox_prevalve = syauto.Valve(auto=auto, cmd="gse_doc_21", ack="gse_doa_21", normally_open=False)

    press_vent = syauto.Valve(auto=auto, cmd="gse_doc_18", ack="gse_doa_18", normally_open=True)

    def run_tpc(auto_):
        fuel_tank_pressure = get_medians(auto_)
        fuel_tpc_1_open = auto_[FUEL_TPC_1_ACK]
        fuel_tpc_2_open = auto_[FUEL_TPC_2_ACK]

        print(f"fuel tank pressure: {fuel_tank_pressure}")
        print(fuel_tpc_1_open, fuel_tpc_2_open)

        if time.time() - START_TPC > 25:
            print("time is up")
            return True

        if fuel_tank_pressure > 460:
            syauto.open_close_many_valves(auto_, [], [fuel_tpc_1, fuel_tpc_2])
            print("TPC 1: CLOSED | TPC 2: CLOSED")

        if fuel_tank_pressure < 440:
            syauto.open_close_many_valves(auto_, [fuel_tpc_1], [])
            print("TPC 1: OPEN")

        if fuel_tank_pressure > 440:
            syauto.open_close_many_valves(auto_, [], [fuel_tpc_2])
            print("TPC 2: CLOSED")

        if fuel_tank_pressure < 420:
            syauto.open_close_many_valves(auto_, [fuel_tpc_1, fuel_tpc_2], [])
            print("TPC 1: OPEN | TPC 2: OPEN")

        # if the pressure drops below 15, the tanks are mostly empty and the test is finished
        if fuel_tank_pressure <= MINIMUM:
            print(f"median pressure invalid - ABORTING")
            syauto.close_all(auto_, [fuel_tpc_1, fuel_tpc_2])
            return True

    try:
        start = sy.TimeStamp.now()

        print("Starting Fuel Bang Bang Coldflow Sequence. Setting initial system state.")
        # set initial system state
        syauto.close_all(auto, [fuel_vent, ox_low_flow_vent, fuel_tpc_1, fuel_tpc_2, fuel_prevalve, fuel_pre_press, ox_drain])  # FUEL + OX
        # syauto.close_all(auto, [fuel_vent, fuel_tpc_1, fuel_tpc_2, fuel_prevalve, fuel_pre_press])  # FUEL 
        print("All valves and vents closed. Beginning test")

        pressure = get_medians(auto)
        if pressure < TARGET_2:
            print("Opening Prevalves")
            syauto.open_all(auto, [fuel_prevalve, ox_prevalve])  # FUEL + OX
            # syauto.open_all(auto, [fuel_prevalve])  # FUEL ONLY
            # time.sleep(1)

        print("Initiating TPC")

        syauto.open_all(auto, [ox_press_iso, ox_dome_iso])  # OX
        auto.wait_until(run_tpc)  

        print("Test complete. Safing System")

        # Create a range in the autosequence
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Fuel Bang Bang Coldflow Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

        # syauto.open_close_many_valves(auto, [ox_low_flow_vent, fuel_vent, ox_drain, press_vent], [fuel_tpc_1, fuel_tpc_2, fuel_prevalve, fuel_pre_press, ox_press_iso, ox_dome_iso, ox_prevalve])
        print("safing Fuel system")
        syauto.open_close_many_valves(auto, [fuel_vent], [fuel_tpc_1, fuel_tpc_2, fuel_prevalve, fuel_pre_press])
        input("Press any key to safe the OX system")
        print("safing OX system")
        syauto.open_close_many_valves(auto, [ox_low_flow_vent, ox_drain, press_vent], [ox_press_iso, ox_dome_iso, ox_prevalve])

    except KeyboardInterrupt:

        print("Test interrupted")
        print("safing Fuel system")
        syauto.open_close_many_valves(auto, [fuel_vent], [fuel_tpc_1, fuel_tpc_2, fuel_prevalve, fuel_pre_press] )
        print("safing OX system")
        syauto.open_close_many_valves(auto, [ox_low_flow_vent, ox_drain, press_vent], [ox_press_iso, ox_dome_iso, ox_prevalve])

    print("Autosequence complete")