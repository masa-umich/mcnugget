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
client = sy.Synnax(
    host="synnax.masa.engin.umich.edu",
    port=80,
    username="synnax",
    password="seldon",
    secure=True
)

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

for i in range(1, 28):
    WRITE_TO.append(f"gse_doc_{i}")
    READ_FROM.append(f"gse_doa_{i}")

for i in range(1,36):
    READ_FROM.append(f"gse_ai_{i}")

#Change these based on testing requirements
TARGET_1 = 90
BOUND_1 = TARGET_1 - 2
INC_1 = 10

TARGET_2 = BOUND_1 - 2
BOUND_2 = TARGET_2 - 2
INC_2 = 30

MAXIMUM = TARGET_1 + 20
MINIMUM = BOUND_2 - 20

# this initializes a connection to the client with access to all the needed channels
with client.control.acquire(name="bang_bang_tpc", write=WRITE_TO, read=READ_FROM) as auto:
    fuel_tpc_1 = syauto.Valve(auto=auto, cmd=FUEL_TPC_1_CMD, ack=FUEL_TPC_1_ACK, normally_open=False)
    fuel_tpc_2 = syauto.Valve(auto=auto, cmd=FUEL_TPC_2_CMD, ack=FUEL_TPC_2_ACK, normally_open=False)
    fuel_prevalve = syauto.Valve(auto=auto, cmd=FUEL_PREVALVE_CMD, ack=FUEL_PREVALVE_ACK, normally_open=False)
    fuel_vent = syauto.Valve(auto=auto, cmd=FUEL_VENT_CMD, ack=FUEL_VENT_ACK, normally_open=True)
    ox_low_flow_vent = syauto.Valve(auto=auto, cmd=OX_LOW_FLOW_VENT_CMD, ack=OX_LOW_FLOW_VENT_ACK, normally_open=True)
    fuel_pre_press = syauto.Valve(auto=auto, cmd=FUEL_PRE_PRESS_VALVE_CMD, ack=FUEL_PRE_PRESS_VALVE_ACK, normally_open=False)

    def run_tpc(auto_: Controller):
        fuel_tank_pressures = syauto.compute_medians(auto,[FUEL_TANK_PT_1, FUEL_TANK_PT_2, FUEL_TANK_PT_3])
        fuel_tpc_1_open = auto_[FUEL_TPC_1_ACK]
        fuel_tpc_2_open = auto_[FUEL_TPC_2_ACK]

        # aborts if the pressure is above the accepted maximum
        if fuel_tank_pressures > MAXIMUM:
            print("pressure has exceeded acceptable range - ABORTING")
            syauto.close_all(auto, [fuel_tpc_1, fuel_tpc_2])
            print ("fuel_tpc_1 and fuel_tpc_2 closed")
            return

        # if pressure is above TARGET_1, closes both valves
        if fuel_tank_pressures > TARGET_1:
            print(f"pressure above {BOUND_1} - closing both valves")
            syauto.close_all(auto, [fuel_tpc_1, fuel_tpc_2])
            print ("fuel_tpc_1 and fuel_tpc_2 closed")

        # if the pressure is below BOUND_1, opens TESCOM_1
        if fuel_tank_pressures < BOUND_1:
            if not fuel_tpc_1_open:
                print(f"pressure below {BOUND_1} - opening valve 1")
                syauto.open(fuel_tpc_1)
                print ("fuel_tpc_1 opened")

        # if the pressure is above TARGET_2, closes TESCOM_2
        if fuel_tank_pressures > TARGET_2:
            if fuel_tpc_2_open:
                print(f"pressure above {TARGET_2} - closing valve 2")
                fuel_tpc_2.close()

        # if the pressure is below BOUND_2, opens TESCOM_2
        if fuel_tank_pressures < BOUND_2:
            if not fuel_tpc_2_open:
                print(f"pressure below {BOUND_2} - opening valve 2")
                fuel_tpc_2.open()

        # if the pressure is below MINIMUM, opens both valves
        if fuel_tank_pressures < MINIMUM:
            if not fuel_tpc_1_open or not fuel_tpc_2_open:
                print(f"pressure below minimum of {MINIMUM} - opening both valves")
                syauto.open_all(auto, [fuel_tpc_1, fuel_tpc_2])
            return

        # if the pressure drops below 15, the tanks are mostly empty and the test is finished
        if fuel_tank_pressures < 15:
            print("pressure below 15 - Tank is empty - ABORTING")
            return

    try:
        print("Starting Fuel Bang Bang Coldflow Sequence. Setting initial system state.")
        #confirm what the initial state of the system should be 
        syauto.close_all(auto, [fuel_vent, ox_low_flow_vent])
        print("fuel vent and ox low flow vent closed")
        time.sleep(2)
        print("Initial state set. Beginning pressurization of fuel tank")

        print(f"Fuel tanks to {TARGET_1} PSI")
        fuel_tpc_1.open()
        # pressurizes press tank and fuel tank to 90 psi in 9 increments
        syauto.pressurize(auto, fuel_pre_press, TARGET_1, INC_1)

        print("Closing fuel tpc valve 1")
        fuel_tpc_1.close()

        # pressurizes press tank to 230 psi in 5 increments
        print("Pressurizing fuel tanks to {TARGET_2} psi")
        syauto.pressurize(auto, fuel_pre_press, TARGET_2, INC_2)

        print("Fuel tanks pressurized to 230 psi - beginning TPC control test in 5")
        time.sleep(2)

        print("Opening MPV")
        fuel_prevalve.open()
        start = sy.TimeStamp.now()

        auto.wait_until(run_tpc)

        print("Test complete. Safing System")

        #Creating a range in the autosequence
        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Fuel Bang Bang Coldflow Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

        syauto.open_close_many_valves(auto, [ox_low_flow_vent, fuel_vent], [fuel_tpc_1, fuel_tpc_2, fuel_prevalve])

    except KeyboardInterrupt:
        print("Test interrupted. Safeing System")
        #close all prevalves and open all vents

    time.sleep(60)