import time
import synnax
from mcnugget.autosequences import syauto

# this initializes a connection to the Synnax server
client = synnax.Synnax()

# these are the channel names we will be using
# we use aliases to make them easier to change later if needed, often we change channels to match avionics stuff
PRESS_VALVE_ACK = "sim_doa_1"
PRESS_VALVE_CMD = "sim_doc_1"
# DOA stands for Digital Output Acknowledgement
# DOC stands for Digital Output Command
# the acknowledgement channel is used to confirm the command was received, representing the state of the valve
# the command channel is used to send UINT8 data representing a command to open or close a valve
PRESS_VENT_ACK = "sim_doa_2"
PRESS_VENT_CMD = "sim_doc_2"
TANK_PRESSURE = "sim_ai_1"
SUPPLY_PRESSURE = "sim_ai_2"
# AI stands for Analog Input
# this kind of channel is used to send FLOAT64 data representing pressure, temperature, etc

# the autosequence will write to the command channels and read from the acknowledgement/pressure channels
WRITE_TO = [PRESS_VENT_CMD, PRESS_VALVE_CMD]
READ_FROM = [PRESS_VENT_ACK, PRESS_VALVE_ACK, TANK_PRESSURE, SUPPLY_PRESSURE]

# the pressure we are going to pressurize to
TARGET = 500

# this acquires control of the autosequence, creating a controller which we can use to interact with the system
auto = client.control.acquire(name="Demo Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100)

print("initializing")
time.sleep(1)

# this creates a valve object which we can use to open and close the valve
# syauto is a utility library we made to abstract away some of the more confusing parts of the controller
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

# this is a function which returns true if the tank pressure is greater than the target pressure
# we will use this later to automatically close the valve when the target pressure is reached
def pressurize(auto: synnax.control.Controller):
    return auto[TANK_PRESSURE] > TARGET

try:
    # good idea to add some safety checks
    input("confirm you would like to start autosequence (press enter)")
    print("setting system state")

    # often want to start by closing everything
    press_valve.close()
    press_vent.close()

    # this opens the press_valve, waits until pressurize returns true, then closes the press_valve
    # synnax automatically applies the necessary Controller functions when we pass in a function like `pressurize`
    print(f"pressurizing to {TARGET} psi")
    press_valve.open()
    auto.wait_until(pressurize)
    press_valve.close()
    print("pressurization complete")

except KeyboardInterrupt as e:
    # if the user interrupts the program, we want to safe the system instead of just stopping immediately
    if str(e) == "Interrupted by user.":
        print("aborting")
        # generally, safing the system means deenergizing everything
        press_valve.close()
        press_vent.open()
        print("system has been safed")

# this disposes of the controller
auto.release()
print("terminating")
time.sleep(1)
