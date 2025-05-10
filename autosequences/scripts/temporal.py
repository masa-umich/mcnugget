import synnax
from autosequences import syauto
import time

client = synnax.Synnax()

WRITES = []
STATES = []
VALVES = []
for i in range(40):
    try:
        write_chan = f"gse_vlv_{i}"
        state_chan = f"gse_state_{i}"
        client.channels.retrieve(write_chan)
        client.channels.retrieve(state_chan)
        WRITES.append(write_chan)
        STATES.append(state_chan)
    except:
        continue

exceptions = 0
with client.control.acquire(
    "Testing Sequence",
    STATES,
    WRITES,
    200
) as auto:
        for i in range(len(WRITES)):
            write = WRITES[i]
            state = STATES[i]
            VALVES.append(syauto.Valve(
                auto, write, state, False
            ))

        while True:
            try:
                for valve in VALVES:
                    valve.open()
                    time.sleep(0.2)
                for valve in VALVES:
                    valve.close()
                    time.sleep(0.2)
                time.sleep(5)
            except Exception as e:
                print(f"encountered an error at {time.time()}")
                print(e)
                exceptions += 1
                if exceptions > 10:
                    print("too many exceptions, exiting")
                    break