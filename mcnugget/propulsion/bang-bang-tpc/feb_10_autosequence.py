'''
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
'''

import time
import synnax as sy
from synnax.control.controller import Controller
import auto_utilities

PRESS_STEP_DELAY = (1 * sy.TimeSpan.SECOND).seconds  # Seconds

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

TESCOM_1_CMD = "gse_doc_1"
TESCOM_1_ACK = "gse_doa_1"
TESCOM_2_CMD = "gse_doc_2"
TESCOM_2_ACK = "gse_doa_2"
SCUBA_CMD = "gse_doc_3"
VENT_CMD = "gse_doc_4"
MPV_CMD = "gse_doc_5"
SCUBA_PT = "gse_ai_1"
L_STAND_PT = "gse_ai_2"

# MINIMUM < BOUND_2 < TARGET_2 < BOUND_1 < TARGET_1 < MAXIMUM

TARGET_1 = 425
BOUND_1 = 417.5                 
TARGET_2 = 410
BOUND_2 = 402.5
MAXIMUM = TARGET_1 + 20
MINIMUM = BOUND_2 - 20

# this function initializes `auto` for the channels specified
with client.control.acquire(
        "bang_bang_tpc",
        write=[
            TESCOM_1_CMD,
            TESCOM_2_CMD,
            SCUBA_CMD,
            VENT_CMD,
            MPV_CMD,
        ],
        read=[
            TESCOM_1_ACK,
            TESCOM_2_ACK,
            SCUBA_PT,
            L_STAND_PT,
        ],
        write_authorities=[255]
    ) as auto:

    TESCOM_1 = auto_utilities.Valve(auto=auto, name="tescom 1", cmd=TESCOM_1_CMD, ack=TESCOM_1_ACK, 
                                    default_open=False, mawp=MAXIMUM, requires_confirm=False)
    TESCOM_2 = auto_utilities.Valve(auto=auto, name="tescom 2", cmd=TESCOM_2_CMD, ack=TESCOM_2_ACK, 
                                    default_open=False, mawp=MAXIMUM, requires_confirm=False)
    ISO_PRESS = auto_utilities.Valve(auto=auto, name="ISO Press", cmd=SCUBA_CMD, ack=None, 
                                    default_open=False, mawp=MAXIMUM, requires_confirm=False)
    MPV = auto_utilities.Valve(auto=auto, name="MPV", cmd=MPV_CMD, ack=None, 
                                    default_open=False, mawp=MAXIMUM, requires_confirm=False)
    VENT = auto_utilities.Valve(auto=auto, name="MPV Vent", cmd=VENT_CMD, ack=None, 
                                    default_open=True, mawp=MAXIMUM, requires_confirm=False)


    def run_tpc(auto: Controller):
        pressure = auto[L_STAND_PT]
        one_open = auto[TESCOM_1_ACK]
        two_open = auto[TESCOM_2_ACK]

        while True:
            # aborts if the pressure is above the accepted maximum
            if pressure > MAXIMUM:
                print("pressure has exceeded acceptable range - ABORTING")
                TESCOM_1.de_energize()
                TESCOM_2.de_energize()
                break

            # if pressure is above TARGET_1, closes both valves
            if pressure > TARGET_1:
                if one_open or two_open:
                    print(f"pressure above {BOUND_1} - closing both valves")
                    TESCOM_1.de_energize()
                    TESCOM_2.de_energize()

            # if the pressure is below BOUND_1, opens TESCOM_1
            if pressure < BOUND_1:
                if not one_open:
                    print(f"pressure below {BOUND_1} - opening valve 1")
                    TESCOM_1.energize()
                
            # if the pressure is above TARGET_2, closes TESCOM_2
            if pressure > TARGET_2:
                if two_open:
                    print(f"pressure above {TARGET_2} - closing valve 2")
                    TESCOM_2.de_energize()

            # if the pressure is below BOUND_2, opens TESCOM_2
            if pressure < BOUND_2:
                if not two_open:
                    print(f"pressure below {BOUND_2} - opening valve 2")
                    TESCOM_2.energize()

            # if the pressure is below MINIMUM, opens both valves
            if pressure < MINIMUM:
                if not one_open or not two_open:
                    print(f"pressure below minimum of {MINIMUM} - opening both valves")
                    TESCOM_1.energize()
                    TESCOM_2.energize()

            # if the pressure drops below 15, the tanks are mostly empty and the test is finished
            return pressure < 15

    try:
        print("Starting TPC Test. Setting initial system state.")
        ISO_PRESS.de_energize()
        TESCOM_1.de_energize()
        TESCOM_2.de_energize()
        MPV.de_energize()
        VENT.de_energize()

        time.sleep(2)

        print(f"Pressing SCUBA and L-Stand to 80 PSI")
        TESCOM_1.energize()
        TESCOM_2.energize()
        ISO_PRESS.energize()
        # pressurizes SCUBA (and L-stand by extension) to 80 psi in 8 increments
        ISO_PRESS.pressurize(SCUBA_PT, 80, 10)
        
        print("closing TESCOMS and pressing SCUBA to 425 psi")
        TESCOM_1.de_energize()
        TESCOM_2.de_energize()
        # pressurizes SCUBA to 425 psi in 10 increments
        ISO_PRESS.pressurize(SCUBA_PT, 425, 34.5)
        
        # closes ISO_PRESS in preparation for TPC control
        ISO_PRESS.de_energize()

        print("SCUBA pressurized to 425 psi - beginning TPC control in 5")
        time.sleep(1)
        print("4")
        time.sleep(1)
        print("3")
        time.sleep(1)
        print("2")
        time.sleep(1)
        print("1")
        time.sleep(1)

        print("Opening MPV")
        MPV.energize()
        start = sy.TimeStamp.now()  

        auto.wait_until(run_tpc())

        print("Test complete. Safeing System")

        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Bang Bang TPC Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

        ISO_PRESS.de_energize()
        TESCOM_1.energize()
        TESCOM_2.energize()
        VENT.energize()
        MPV.energize()

    except KeyboardInterrupt:
        print("Test interrupted. Safeing System")
        ISO_PRESS.de_energize()
        TESCOM_1.energize()
        TESCOM_2.energize()
        VENT.energize()
        MPV.energize()

    print("end of autosequence - waiting 60 seconds")