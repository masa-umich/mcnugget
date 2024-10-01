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


target_pressure = 0

#declaring globals so synnax can find them
global temp_target_pressure
temp_target_pressure = 0

global CURR_PRESSURE
CURR_PRESSURE = 0

global PREV_PRESSURE
PREV_PRESSURE = 0

global BURST
BURST = False

# this acquires control of the autosequence, creating a controller which we can use to interact with the system
auto = client.control.acquire(name="Demo Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100)

print("initializing...")
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

#returns true if tank pressure is greater than target pressure
def pressurize(auto: synnax.control.Controller):
    return auto[TANK_PRESSURE] > target_pressure

#returns true if tank pressure is greater than a temp (frequently modified) target pressure
def temp_pressurize(auto):
     return auto[TANK_PRESSURE] > temp_target_pressure

#pressurizes tank in increments of 50 for when there is a specified target pressure
def base_inc_pressurize(auto):
    global temp_target_pressure
    while auto[TANK_PRESSURE] + 50 < target_pressure:
        press_valve.open()
        temp_target_pressure += 50
        auto.wait_until(temp_pressurize)
        press_valve.close()
        time.sleep(3) 
    press_valve.open()
    auto.wait_until(pressurize)
    press_valve.close()
    return True     

#creturns true if there's a sudden drop in pressure
def drop(auto):
    global CURR_PRESSURE
    global PREV_PRESSURE

    PREV_PRESSURE = CURR_PRESSURE
    CURR_PRESSURE = auto[TANK_PRESSURE]

    return (((CURR_PRESSURE - PREV_PRESSURE) + 100) < 0)

#returns true if either (a) temp target pressure is reached or (b) the tank has burst
def check_drop(auto):
     global BURST

     if auto[TANK_PRESSURE] > temp_target_pressure:
          return True
     if drop(auto):
          BURST = True
          return True

#incremental pressurization for unspecified target pressure
def inc_pressurize(auto):
     global temp_target_pressure
     temp_target_pressure += 50
     while not drop(auto):
        press_valve.open()
        auto.wait_until(check_drop)
        if BURST:
             break
        press_valve.close()
        temp_target_pressure += 50
        time.sleep(3)
     return True
    

try:
    # good idea to add some safety checks
    input("confirm you would like to start autosequence (press enter)")
    print("setting system state\n")

    # start by closing everything
    press_valve.close()

    print("pressurizing to MAWP (850 psi)")
    target_pressure = 850
    base_inc_pressurize(auto)
    print(f"pressurized to {auto[TANK_PRESSURE]}\n")
    time.sleep(5)

    print("pressurizing to 1.1x MAWP (935 psi)")
    target_pressure = 850 * 1.1
    base_inc_pressurize(auto)
    print(f"pressurized to {auto[TANK_PRESSURE]}\n")
    time.sleep(600)
    input("continue?")

    print("pressurizing to burst...")
    press_valve.open()
    PREV_PRESSURE = CURR_PRESSURE
    CURR_PRESSURE = auto[TANK_PRESSURE]
    inc_pressurize(auto)
    press_valve.close()
    print(f"burst at {PREV_PRESSURE}")



except KeyboardInterrupt as e:
    # if the user interrupts the program, we want to safe the system instead of just stopping immediately
        print("Interrupted by user.")
        print("aborting")
        # generally, safing the system means deenergizing everything
        press_valve.close()
        press_vent.open()

        print("system has been safed")