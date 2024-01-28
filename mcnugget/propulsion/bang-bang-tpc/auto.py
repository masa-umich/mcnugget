import time
import synnax as sy
from synnax.control.controller import Controller

# TPC Control Bound
BOUND = 5  # PSI
TPC_UPPER_BOUND = 50  # PSI
TPC_LOWER_BOUND = TPC_UPPER_BOUND - BOUND

L_STAND_PRESS_TARGET = 65
SCUBA_PRESS_TARGET = 275  # PSI

PRESS_1_STEP = 10  # PSI
PRESS_2_STEP = 50  # PSI

PRESS_STEP_DELAY = (1 * sy.TimeSpan.SECOND).seconds  # Seconds

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)


def run_tpc(auto: Controller):
    pressure = auto[L_STAND_PT]
    one_open = auto[TPC_CMD_ACK]

    if pressure > TPC_UPPER_BOUND:
        if one_open:
            auto[TPC_CMD] = False
    elif pressure < TPC_LOWER_BOUND:
        auto[TPC_CMD] = True

    return pressure < 15


TPC_CMD = "gse_doc_1"
TPC_CMD_ACK = "gse_doa_1"
MPV_CMD = "gse_doc_2"
PRESS_ISO_CMD = "gse_doc_3"
# Normally open
VENT_CMD = "gse_doc_4"

SCUBA_PT = "gse_ai_1"
L_STAND_PT = "gse_ai_2"

with client.control.acquire(
        "Autosequence",
        write=[
            TPC_CMD,
            MPV_CMD,
            PRESS_ISO_CMD,
            VENT_CMD
        ],
        read=[TPC_CMD_ACK, SCUBA_PT, L_STAND_PT],
        write_authorities=[250]
) as auto:
    try:
        print("Starting TPC Test. Setting initial system state.")
        auto.set({
            TPC_CMD: 0,
            MPV_CMD: 0,
            PRESS_ISO_CMD: 0,
            VENT_CMD: 1,
        })

        time.sleep(2)

        print(f"Pressing SCUBA and L-Stand to 50 PSI")

        # Pressurize l-stand and scuba to 50 PSI
        # Open TPC Valve
        auto[TPC_CMD] = True

        curr_target = PRESS_1_STEP
        while True:
            print(f"Pressing L-Stand to {curr_target} PSI")
            auto[PRESS_ISO_CMD] = True
            auto.wait_until(lambda c: c[L_STAND_PT] > curr_target)
            auto[PRESS_ISO_CMD] = False
            curr_target += PRESS_1_STEP
            curr_target = min(curr_target, L_STAND_PRESS_TARGET)
            if auto[L_STAND_PT] > L_STAND_PRESS_TARGET:
                break
            print("Taking a nap")
            time.sleep(PRESS_STEP_DELAY)

        print("Pressurized. Waiting for five seconds")
        time.sleep(PRESS_STEP_DELAY)
        # ISO off TESCOM and press scuba with ISO
        auto[TPC_CMD] = False

        curr_target = L_STAND_PRESS_TARGET + PRESS_2_STEP
        while True:
            auto[PRESS_ISO_CMD] = True
            auto.wait_until(lambda c: c[SCUBA_PT] > curr_target)
            auto[PRESS_ISO_CMD] = False
            curr_target += PRESS_2_STEP
            curr_target = min(curr_target, SCUBA_PRESS_TARGET)
            if auto[SCUBA_PT] > SCUBA_PRESS_TARGET:
                break
            print("Taking a nap")
            time.sleep(PRESS_STEP_DELAY)

        print("Pressurized. Waiting for five seconds")
        time.sleep(2)

        # auto.wait_until(lambda c: c[L_STAND_PT] < 51)

        start = sy.TimeStamp.now()

        print("Opening MPV")
        auto[MPV_CMD] = 1
        auto.wait_until(lambda c: run_tpc(c))
        print("Test complete. Safeing System")

        rng = client.ranges.create(
            name=f"{start.__str__()[11:16]} Bang Bang TPC Sim",
            time_range=sy.TimeRange(start, sy.TimeStamp.now()),
        )

        auto.set({
            TPC_CMD: 1,
            PRESS_ISO_CMD: 0,
            # Open vent
            VENT_CMD: 0,
            MPV_CMD: 0,
        })
        time.sleep(100)
    except KeyboardInterrupt:
        print("Test interrupted. Safeing System")
        auto.set({
            TPC_CMD: 1,
            PRESS_ISO_CMD: 0,
            # Open vent
            VENT_CMD: 0,
            # Leave MPV open
            MPV_CMD: 1,
        })

