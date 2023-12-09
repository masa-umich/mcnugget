import time
import synnax as sy
from synnax.control.controller import Controller

CLOSE_ALL_THRESHOLD = 250
VALVE_1_THRESHOLD = 250 - 10
VALVE_2_THRESHOLD = 250 - 20
PT = "pressure"

PRESS_TARGET = 250
PRESS_STEP = 250
PRESS_STEP_DELAY = (2 * sy.TimeSpan.SECOND).seconds

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)



def run_tpc(auto: Controller):
    pressure = auto["pressure"]
    one_open = auto["tpc_vlv_1_ack"]
    two_open = auto["tpc_vlv_2_ack"]

    if pressure > CLOSE_ALL_THRESHOLD:
        if one_open or two_open:
            print("CLOSING ALL VALVES")
            auto.set({
                "tpc_vlv_1_cmd": 0,
                "tpc_vlv_2_cmd": 0,
            })
    elif pressure < VALVE_2_THRESHOLD:
        if not one_open or not two_open:
            print("OPENING ALL VALVES")
            auto.set({
                "tpc_vlv_1_cmd": 1,
                "tpc_vlv_2_cmd": 1,
            })
    elif pressure < VALVE_1_THRESHOLD:
        if not one_open:
            print("OPENING VALVE 1")
            auto.set({"tpc_vlv_1_cmd": 1})

    return pressure < 15


with client.control.acquire(
        "bang_bang_tpc",
        write=[
            "tpc_vlv_1_cmd",
            "tpc_vlv_2_cmd",
            "mpv_cmd",
            "press_vlv_cmd",
            "vent_vlv_cmd",
        ],
        read=["pressure", "tpc_vlv_1_ack", "tpc_vlv_2_ack"],
        write_authorities=[255]
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

    # Pressurize the l-stand
    curr_target = PRESS_STEP
    while True:
        auto["press_vlv_cmd"] = True
        auto.wait_until(lambda c: c.pressure > curr_target)
        auto["press_vlv_cmd"] = False
        curr_target += PRESS_STEP
        if auto["pressure"] > PRESS_TARGET:
            break
        time.sleep(PRESS_STEP_DELAY)

    print("Pressurized. Waiting for five seconds")
    time.sleep(3)

    print("Opening MPV")
    auto["mpv_cmd"] = 1
    auto.wait_until(lambda c: run_tpc(c))
    print("Test complete. Safeing System")

    auto.set({
        "tpc_vlv_1_cmd": 0,
        "tpc_vlv_2_cmd": 0,
        "press_vlv_cmd": 0,
        "mpv_cmd": 1,
        "vent_vlv_cmd": 1,
    })
