import time
import synnax
from mcnugget.autosequences import syauto

client = synnax.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
)

PRESS_VALVE_ACK = "sim_doa_1"
PRESS_VALVE_CMD = "sim_doc_1"
PRESS_VENT_ACK = "sim_doa_2"
PRESS_VENT_CMD = "sim_doc_2"
PRESS_TANK = "sim_ai_1"
PRESS_SUPPLY = "sim_ai_2"

WRITE_TO = [PRESS_VENT_CMD, PRESS_VALVE_CMD]
READ_FROM = [PRESS_VENT_ACK, PRESS_VALVE_ACK, PRESS_TANK, PRESS_SUPPLY]

TARGET = 500

# auto = client.control.acquire(name="Demo Autosequence", write=WRITE_TO, read=READ_FROM, write_authorities=100)
auto = client.control.acquire(name="Demo Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100)

print("initializing")
time.sleep(1)

press_valve = syauto.Valve(
    auto=auto,
    cmd=PRESS_VALVE_CMD,
    ack=PRESS_VALVE_ACK,
    normally_open=False,
)

press_vent = syauto.Valve(
    auto=auto,
    cmd=PRESS_VENT_CMD,
    ack=PRESS_VENT_ACK,
    normally_open=True,
)

def pressurize(auto: synnax.control.Controller):
        return auto[PRESS_TANK] > TARGET


try:
    input("confirm you would like to start autosequence (press enter)")
    print("setting system state")

    press_valve.close()
    press_vent.close()

    print(f"pressurizing to {TARGET} psi")
    # auto[PRESS_VALVE_CMD] = 1
    press_valve.open()
    auto.wait_until(pressurize)
    press_valve.close()

except KeyboardInterrupt as e:
    if str(e) == "Interrupted by user.":
        print("aborting")
        press_valve.close()
        press_vent.open()

auto.release()
print("terminating")
time.sleep(10)
