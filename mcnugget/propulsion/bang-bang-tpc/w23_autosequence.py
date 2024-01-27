import time
import synnax as sy
from synnax.control.controller import Controller

# CLOSE_ALL_THRESHOLD = 250               # threshold at which everything stops

V1_TARGET = 500                    # MEOP for v1
V1_MAX = 1000                      # MAWP for v1
V1_CHANNEL = "gse_vlv_1"       # name of channel for v1
V1_ACK = V1_CHANNEL + "_ack"
V1_CMD = V1_CHANNEL + "_cmd"
V1_PRESS = ""                       # TODO: define this

V2_TARGET = 50                     # MEOP for v2
V2_MAX = 250                       # MAWP for v2
V2_CHANNEL = "gse_vlv_2"       # name of channel for v2
V2_ACK = V2_CHANNEL + "_ack"
V2_CMD = V2_CHANNEL + "_cmd"
V2_PRESS = ""                       # TODO: define this

VENT_CHANNEL = "gse_vent"
VENT_CMD = VENT_CHANNEL + "_cmd"


PRESS_STEP_DELAY = (2 * sy.TimeSpan.SECOND).seconds

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)


def pressurize_v1_v2(auto: Controller) -> bool:
    open_1 = auto[V1_ACK]
    open_2 = auto[V2_ACK]
    press_1 = auto["pressure1?"]            # TODO: figure out correct pressure readings
    press_2 = auto["pressure2?"]

    if press_1 > V1_MAX:
        if open_1:
            print(f"closing {V1_CHANNEL} due to high pressure")
            auto.set({
                V1_CMD: 0
            })

    if press_2 > V2_MAX:
        if open_2:
            print(f"closing {V2_CHANNEL} due to high pressure")
            auto.set({
                V2_CMD: 0
            })

    if press_1 < V1_TARGET:
        if not open_1:
            print(f"opening {V1_CHANNEL} to increase pressure")
            auto.set({
                V1_CMD: 1
            })

    if press_2 < V2_TARGET:
        if not open_2:
            print(f"opening {V2_CHANNEL} to increase pressure")
            auto.set({
                V2_CMD: 1
            })

    return press_1 < 15 and press_2 < 15


print("beginning sequence")
with client.control.acquire(
        "bangbang-tpc",                 # TODO: change this to match testing
        write=[
            V1_CMD,
            V2_CMD,
            # PRESSURES
            # VENTS
        ],
        read=[V1_ACK, V2_ACK],                  # TODO: add press channels
        write_authorities=[255]             # don't know what this is so im leaving it
) as auto:
    # Make sure we're in a good starting state
    auto.set({
        "tpc_vlv_1_cmd": 0,
        "tpc_vlv_2_cmd": 0,
        "mpv_cmd": 0,
        "press_vlv_cmd": 0,
        "vent_vlv_cmd": 0,
    })

    print("Waiting for pressure to drop")

    auto.wait_until(lambda c: pressurize_v1_v2(c))

    print("finished pressurizing")

    print("Test complete. Safeing System")
    auto.set({
        "tpc_vlv_1_cmd": 0,
        "tpc_vlv_2_cmd": 0,
        "press_vlv_cmd": 0,
        "mpv_cmd": 1,
        "vent_vlv_cmd": 1,
    })