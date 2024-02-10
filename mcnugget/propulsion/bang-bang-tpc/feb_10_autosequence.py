""""
valve_1 and valve_2 correspond to the valves between the Acc. Press and the L-stand

2k Bottle Supply (source)
Acc. Press + valve
L-stand + 2 valves
L-stand MPV (valve)
L-stand Vent (valve)

1. initializes client for all valves needed
2. pressurize acc. press to ???
3. pressurize L-stand using TPC logic while keeping acc. press at target as well
4. close valves to seal L-stand
5. open MPV
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

TPC_1_OPEN_CMD = "gse_doc_6"
TPC_1_OPEN_ACK = "gse_doa_6"
TPC_1_CLOSE_CMD = "gse_doc_5"
TPC_1_CLOSE_ACK = "gse_doa_5"
TPC_2_OPEN_CMD = "gse_doc_10"
TPC_2_OPEN_ACK = "gse_doa_10"
TPC_2_CLOSE_CMD = "gse_doc_7"
TPC_2_CLOSE_ACK = "gse_doa_7"
PRESS_ISO_CMD = "gse_doc_11"
VENT_CMD = "gse_doc_8"
MPV_CMD = "gse_doc_9"
SCUBA_PT = "gse_ai_8"
L_STAND_PT = "gse_ai_1"

WRITE_TO = [TPC_1_CLOSE_CMD, TPC_1_OPEN_CMD, TPC_2_CLOSE_CMD, TPC_2_OPEN_CMD, PRESS_ISO_CMD, VENT_CMD, MPV_CMD]
READ_FROM = [TPC_1_CLOSE_ACK, TPC_1_OPEN_ACK, TPC_2_CLOSE_ACK, TPC_2_OPEN_ACK, SCUBA_PT, L_STAND_PT]

TARGET_1 = 80
BOUND_1 = TARGET_1 - 10
TARGET_2 = BOUND_1 - 10
BOUND_2 = TARGET_2 - 10
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
        print(f"Pressing SCUBA and L-Stand to 80 PSI")
        tpc_vlv_1.open()
        # pressurizes press tank and fuel tank to 80 psi in 8 increments
        syauto.pressurize(press_iso, L_STAND_PT, 80, 10)

        print("Closing tpc valves and pressing SCUBA to 425 psi")
        tpc_vlv_1.close()

        # pressurizes press tank to 425 psi in 10 increments
        syauto.pressurize(press_iso, SCUBA_PT, 425, 34.5)

        print("SCUBA pressurized to 425 psi - beginning TPC control test in 5")
        time.sleep(5)

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
