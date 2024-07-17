""""
TPCs: 
- 2x dual opening valves for fuel
- 3x dual valves for oxygen 
"""

import time
import synnax as sy
from synnax.control.controller import Controller
import syauto

PRESS_STEP_DELAY = (1 * sy.TimeSpan.SECOND).seconds  # Seconds

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)
#oxygen valves
OX_1_SUPPLY_CMD = "gse_doc_1"  #change these based on testing
OX_1_SUPPLY_ACK = "gse_doa_1"
OX_1_VENT_CMD = "gse_doc_2"
OX_1_VENT_ACK = "gse_doa_2"
OX_2_SUPPLY_CMD = "gse_doc_3" 
OX_2_SUPPLY_ACK = "gse_doa_3"
OX_2_VENT_CMD = "gse_doc_4"
OX_2_VENT_ACK = "gse_doa_4"

#fuel valves
FUEL_1_SUPPLY_CMD = "gse_doc_5" #change these based on testing
FUEL_1_SUPPLY_ACK = "gse_doa_5" 
FUEL_1_VENT_CMD = "gse_doc_6"
FUEL_1_VENT_ACK = "gse_doa_6"
FUEL_2_SUPPLY_CMD = "gse_doc_7"
FUEL_2_SUPPLY_ACK = "gse_doa_7"
FUEL_2_VENT_CMD = "gse_doc_8"
FUEL_2_VENT_ACK = "gse_doa_8"
FUEL_3_SUPPLY_CMD = "gse_doc_9"
FUEL_3_SUPPLY_ACK = "gse_doa_9"
FUEL_3_VENT_CMD = "gse_doc_10"
FUEL_3_VENT_ACK = "gse_doa_10"

PRESS_ISO_CMD = "gse_doc_11"
PRESS_ISO_ACK = "gse_doa_11"
VENT_CMD = "gse_doc_12"
MPV_CMD = "gse_doc_13"
SCUBA_PT = "gse_ai_8"
L_STAND_PT = "gse_ai_1"

#writing to valve command channels
WRITE_TO = [FUEL_1_SUPPLY_CMD, FUEL_1_VENT_CMD, FUEL_2_SUPPLY_CMD, FUEL_2_VENT_CMD, 
            FUEL_3_SUPPLY_CMD, FUEL_3_VENT_CMD, 
            OX_1_SUPPLY_CMD, OX_1_VENT_CMD, OX_2_SUPPLY_CMD, OX_2_VENT_CMD, 
            PRESS_ISO_CMD, VENT_CMD, MPV_CMD]

#reading from valve acknowledgement and PT channels
READ_FROM = [FUEL_1_SUPPLY_ACK, FUEL_1_VENT_ACK, FUEL_2_SUPPLY_ACK, FUEL_2_VENT_ACK,
            FUEL_3_SUPPLY_ACK, FUEL_3_VENT_ACK,
            OX_1_SUPPLY_ACK, OX_1_VENT_ACK, OX_2_SUPPLY_ACK, OX_2_VENT_ACK,
            SCUBA_PT, L_STAND_PT]

#defining targent pressues and bounds
TARGET_1 = 90 #change these based on P&ID and Testing
BOUND_1 = TARGET_1 - 2
TARGET_2 = BOUND_1 - 2
BOUND_2 = TARGET_2 - 2
MAXIMUM = TARGET_1 + 20
MINIMUM = BOUND_2 - 20

# this initializes a connection to the client with access to all the needed channels
with client.control.acquire(name="bang_bang_tpc", write=WRITE_TO, read=READ_FROM) as auto:
    tpc_vlv_1 = syauto.DualTescomValve(auto=auto, open_cmd_chan=TPC_1_OPEN_CMD, close_cmd_chan=TPC_1_CLOSE_CMD,
                                       open_cmd_ack=TPC_1_OPEN_ACK, close_cmd_ack=TPC_1_CLOSE_ACK)
    tpc_vlv_2 = syauto.DualTescomValve(auto=auto, open_cmd_chan=TPC_2_OPEN_CMD, close_cmd_chan=TPC_2_CLOSE_CMD,
                                       open_cmd_ack=TPC_2_OPEN_ACK, close_cmd_ack=TPC_2_CLOSE_ACK)
    press_iso = syauto.Valve(auto=auto, cmd=PRESS_ISO_CMD)
    mpv = syauto.Valve(auto=auto, cmd=MPV_CMD)
    vent = syauto.Valve(auto=auto, cmd=VENT_CMD, normally_open=True)


    def run_tpc(auto_: Controller):
        pressure = auto_[L_STAND_PT]
        one_open = auto_[TPC_1_OPEN_ACK]
        two_open = auto_[TPC_2_OPEN_ACK]

        # aborts if the pressure is above the accepted maximum
        if pressure > MAXIMUM:
            print("pressure has exceeded acceptable range - ABORTING")
            tpc_vlv_1.close()
            tpc_vlv_2.close()
            return

        # if pressure is above TARGET_1, closes both valves
        if pressure > TARGET_1:
            if one_open or two_open:
                print(f"pressure above {BOUND_1} - closing both valves")
                tpc_vlv_1.close()
                tpc_vlv_2.close()

        # if the pressure is below BOUND_1, opens TESCOM_1
        if pressure < BOUND_1:
            if not one_open:
                print(f"pressure below {BOUND_1} - opening valve 1")
                tpc_vlv_1.open()

        # if the pressure is above TARGET_2, closes TESCOM_2
        if pressure > TARGET_2:
            if two_open:
                print(f"pressure above {TARGET_2} - closing valve 2")
                tpc_vlv_2.close()

        # if the pressure is below BOUND_2, opens TESCOM_2
        if pressure < BOUND_2:
            if not two_open:
                print(f"pressure below {BOUND_2} - opening valve 2")
                tpc_vlv_2.open()

        # if the pressure is below MINIMUM, opens both valves
        if pressure < MINIMUM:
            if not one_open or not two_open:
                print(f"pressure below minimum of {MINIMUM} - opening both valves")
                tpc_vlv_1.open()
                tpc_vlv_2.open()

            # if the pressure drops below 15, the tanks are mostly empty and the test is finished
            return pressure < 15


    try:
        print("Starting TPC Test. Setting initial system state.")
        press_iso.close()
        tpc_vlv_1.close()
        tpc_vlv_2.close()
        mpv.close()
        vent.open()

        time.sleep(2)

        vent.close()
        print(f"Pressing SCUBA and L-Stand to " + str(TARGET_1) + " PSI")
        tpc_vlv_1.open()
        # pressurizes press tank and fuel tank to 90 psi in 9 increments
        syauto.pressurize(press_iso, L_STAND_PT, TARGET_1, 10)

        print("Closing tpc valves and pressing SCUBA to 220 psi")
        tpc_vlv_1.close()

        # pressurizes press tank to 230 psi in 5 increments
        syauto.pressurize(press_iso, SCUBA_PT, 230, 30)

        print("SCUBA pressurized to 230 psi - beginning TPC control test in 5")
        time.sleep(2)

        print("Opening MPV")
        mpv.open()
        start = sy.TimeStamp.now()

        auto.wait_until(run_tpc)

        print("Test complete. Safing System")

        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Bang Bang TPC Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

        press_iso.close()
        tpc_vlv_1.open()
        tpc_vlv_2.open()
        vent.open()
        mpv.open()

    except KeyboardInterrupt:
        print("Test interrupted. Safeing System")
        press_iso.close()
        tpc_vlv_1.open()
        tpc_vlv_2.open()
        vent.open()
        mpv.open()

    time.sleep(60)