import synnax as sy
import time

client = sy.Synnax()

# Define valve commands and states
VALVES = {f"gse_vlv_{i}": f"gse_state_{i}" for i in range(1, 25) if i not in [5, 16]}

# Prepare lists for control acquisition
WRITE_TO = list(VALVES.keys())
READ_FROM = list(VALVES.values())

with client.control.acquire(
    name="Valve Control Sequence",
    write=WRITE_TO,
    read=READ_FROM,
    write_authorities=222
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
        print("Starting Valve Control Sequence")
        
        # Open all valves
        operate_valves(open_valves=True)
        
        # Wait for 5 seconds
        print("Waiting for 1 second")
        time.sleep(1)
        
        # Close all valves
        operate_valves(open_valves=False)
        
        print("Valve Control Sequence completed")
    
    except KeyboardInterrupt:
        print("\nManual abort, closing all valves")
        operate_valves(open_valves=False)
        print("Sequence terminated")

time.sleep(2)
