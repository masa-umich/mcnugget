import synnax
import time
from autosequences import syauto

client = synnax.Synnax()

VALVE = "gse_do_4_1_cmd"
VALVE_STATE = "gse_do_4_1_state"

MPV_OPEN_TIME = 2

input("Type 'start' to start")

# create a channel for the valve
with client.control.acquire("Valve Timing Script", [VALVE]) as auto:
    try:
        print("5")
        time.sleep(1)
        print("4")
        time.sleep(1)
        print("3")
        time.sleep(1)
        print("2")
        time.sleep(1)
        print("1")
        time.sleep(1)
        valve = syauto.Valve(auto, VALVE, VALVE_STATE)
        for i in range(5):
            print("Opening valve")
            valve.open()
            time.sleep(MPV_OPEN_TIME)
            print("Closing valve")
            valve.close()
            input(f"Trial {i} complete. Press enter to continue to trial {i+1}.")

    except KeyboardInterrupt:
        print("Aborting")
        valve.close()
