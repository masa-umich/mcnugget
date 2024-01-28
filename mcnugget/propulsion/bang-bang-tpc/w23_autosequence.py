import time
import synnax as sy
from synnax.control.controller import Controller

# CLOSE_ALL_THRESHOLD = 250               # threshold at which everything stops

# V1_TARGET = 500                           # MEOP for v1
V1_MAX = 1000                               # MAWP for v1
# V1_STEP = 500
V1_CHANNEL = "gse_vlv_1"                    # TODO name of channel for v1
V1_ACK = V1_CHANNEL + "_ack"
V1_CMD = V1_CHANNEL + "_cmd"
V1_PRESS = V1_CHANNEL               # TODO: define this?

# V2_TARGET = 100                           # MEOP for v2
V2_MAX = 250                                # MAWP for v2
# V1_STEP = 20
V2_CHANNEL = "gse_vlv_2"                    # TODO name of channel for v2
V2_ACK = V2_CHANNEL + "_ack"
V2_CMD = V2_CHANNEL + "_cmd"

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


print(f"beginning sequence")
with client.control.acquire(
        "bangbang-tpc",                 # TODO: change this to match testing?
        write=[
            V1_CMD,
            # PRESSURES
            # VENTS
        ],
        read=[V1_ACK, V2_ACK],                  # TODO: add press channels?
        write_authorities=[255]             # don't know what this is so im leaving it
) as auto:
    # Make sure we're in a good starting state
    auto.set({
        V1_CMD: 0,
        V2_CMD: 0,
        "mpv_cmd": 0,
        "press_vlv_cmd": 0,         # TODO
        "vent_vlv_cmd": 0,
    })
    print("Waiting for pressure to drop")


def pressurize(cmd: str, ack: str, target: int, max_p: int, step: int):
    print(f"pressurizing to {target} at step {step} using {cmd}")
    input(f"PRESS ANY KEY TO CONTINUE")
    auto.set(cmd, 1)
    while True:
        auto[cmd] = True
        auto.wait_until(lambda c: runsafe(cmd, ack, target, max_p))
        auto[cmd] = False
        target += step
        if auto["pressure"] > target:
            break
        time.sleep(PRESS_STEP_DELAY)


def runsafe(cmd: str, ack: str, target: int, max_p: int) -> bool:
    valve_open = auto[ack]
    pressure = auto["pressure"]                         #TODO

    if pressure > max_p and valve_open:
        print(f"pressure too high - closing valve using {cmd}")
        auto.set(cmd, 0)

    if pressure < target and not valve_open:
        print(f"opening valve using {cmd}")
        auto.set(cmd, 1)

    return pressure >= target


V1_TARGET = 100
V1_STEP = 20
pressurize(V1_CMD, V1_ACK, V1_TARGET, V1_MAX, V1_STEP)

V1_TARGET = 500
V1_STEP = 50
pressurize(V1_CMD, V1_ACK, V1_TARGET, V1_MAX, V1_STEP)

V2_TARGET = 100
V2_STEP = 20
pressurize(V2_CMD, V2_ACK, V2_TARGET, V1_MAX, V2_STEP)

print("Test complete. Safeing System")
input("PRESS ANY KEY TO CONFIRM")
auto.set({
    "tpc_vlv_1_cmd": 0,
    "tpc_vlv_2_cmd": 0,
    "press_vlv_cmd": 0,         #TODO
    "mpv_cmd": 1,
    "vent_vlv_cmd": 1,
})