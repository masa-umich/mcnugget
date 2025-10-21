import synnax
import time

client = synnax.Synnax()

CHANNEL = "gse_tc_1"

print(f"streaming {CHANNEL}")
with client.open_streamer(CHANNEL) as streamer:
    while True:
        frame = streamer.read(0)
        if frame is not None:
            print(frame[CHANNEL][-1])
        time.sleep(0.01)