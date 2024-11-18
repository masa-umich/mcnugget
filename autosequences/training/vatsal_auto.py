import time
import synnax
import sys
import os
from pynput import keyboard
from autosequences import syauto

# Initialize the connection to the Synnax server
client = synnax.Synnax()

# Define channel names
PRESS_VALVE_ACK = "sim_doa_1"
PRESS_VALVE_CMD = "sim_doc_1"
PRESS_VENT_ACK = "sim_doa_2"
PRESS_VENT_CMD = "sim_doc_2"
TANK_PRESSURE = "sim_ai_1"
SUPPLY_PRESSURE = "sim_ai_2"

# Define the channels to write to and read from
WRITE_TO = [PRESS_VENT_CMD, PRESS_VALVE_CMD]
READ_FROM = [PRESS_VENT_ACK, PRESS_VALVE_ACK, TANK_PRESSURE, SUPPLY_PRESSURE]

# The target pressure to pressurize to
TARGET_PRESSURE = 500
INCREMENT = 100

# Acquire control of the autosequence
auto = client.control.acquire(name="Tank Pressure Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100)

print("Initializing...")
time.sleep(1)

# Ensure required channels have data available before proceeding
auto.wait_until_defined([TANK_PRESSURE, SUPPLY_PRESSURE, PRESS_VALVE_ACK, PRESS_VENT_ACK])

# Create valve objects for the press valve and vent valve
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

# Add these global variables
paused = False
state = {}

# Add the key press handler
def on_key_press(key):
    global paused
    if key == keyboard.Key.space:
        paused = not paused
        if paused:
            print("System paused. Valves and vents are closed.")
        else:
            print("System resumed. Valves and vents restored to saved state.")

# Add keyboard listener after valve definitions
listener = keyboard.Listener(on_press=on_key_press)
listener.start()

# Function to check if the tank pressure has reached the target pressure
def is_target_reached(state, target: int):
    return state[TANK_PRESSURE] >= target

# Function to incrementally increase the tank pressure
def increment_pressure(auto: synnax.control.Controller):
    current_pressure = auto[TANK_PRESSURE]
    target = min(current_pressure + INCREMENT, TARGET_PRESSURE)
    print(f"Pressurizing to {target} psi...")
    press_valve.open()
    auto.wait_until(lambda state: is_target_reached(state, target))
    press_valve.close()
    print(f"Reached {target} psi")
    print("Waiting for 2 seconds...")
    time.sleep(2)  # Add a 2-second break between increments

try:
    input("Confirm you would like to start the autosequence (press enter)")
    print("Setting system state")

    # Start by closing everything
    press_valve.close()
    press_vent.close()

    # Incrementally increase the pressure to the target pressure
    while auto[TANK_PRESSURE] < TARGET_PRESSURE:
        increment_pressure(auto)
        if auto[TANK_PRESSURE] < TARGET_PRESSURE:
            print("Preparing for next increment...")

    print("Target pressure reached")

    # Wait for user confirmation to release the pressure
    input("Confirm to release pressure (press enter)")

    # Open the vent to release the pressure
    print("Releasing pressure...")
    press_vent.open()
    time.sleep(2)  # Give some time to release pressure

except KeyboardInterrupt as e:
    if str(e) == "Interrupted by user.":
        print("Aborting")
        press_valve.close()
        press_vent.open()
        print("System has been safed")

# Dispose of the controller
auto.release()
print("Terminating")
time.sleep(1)