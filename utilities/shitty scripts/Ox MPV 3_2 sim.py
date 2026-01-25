# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax>=0.49,<0.50",
# ]
# ///
import synnax as sy
import time

client = sy.Synnax(host="synnax.masa.engin.umich.edu", port=9090, username="synnax", password="seldon", secure=False)

# Define valve commands and states
VALVES = {f"gse_vlv_{i}": f"gse_state_{i}" for i in [7, 8]}
CON = ("gse_vlv_7", "gse_state_7")
VENT = ("gse_vlv_8", "gse_state_8")

# Prepare lists for control acquisition
WRITE_TO = [VENT[0]]
READ_FROM = list(VALVES.values())

with client.control.acquire(
    name="MPV Ox 3/2", write=WRITE_TO, read=READ_FROM, write_authorities=100
) as auto:

    def operate_valves(open_valves=True):
        operation = "Opening" if open_valves else "Closing"
        for valve_cmd, valve_state in VALVES.items():
            print(f"{operation} valve {valve_cmd}")
            auto[valve_cmd] = 1 if open_valves else 0
            time.sleep(0.1)  # Short delay between valve operations
            if auto[valve_state] != (1 if open_valves else 0):
                print(f"Warning: {valve_cmd} did not {operation.lower()} properly")

    try:
        print("Starting 3/2 Ox MPV")
        last_vent = auto.get(VENT[1])
        while True:
            now_state = auto.get(CON[1])
            if last_vent == now_state:
                print("switching")
                auto[VENT[0]] = not now_state
                last_vent = not now_state
    except KeyboardInterrupt:
        print("\nManual abort")

time.sleep(1)