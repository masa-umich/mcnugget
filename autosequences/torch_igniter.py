from autosequences import syauto
import time
import synnax
import statistics
from collections import deque

client = synnax.Synnax()
# client = synnax.Synnax(
#     host="localhost",
#     port=9090,
#     username="synnax",
#     password="seldon",
#     secure=False
# )

### TEST SPECS ###
MPV_DELAY = 0
IGNITION_THRESHOLD = 200
IGNITION_DURATION = 3
SPARK_LEAD = 3

### VALVES ###
GOX_MPV = 18
METHANE_MPV = 16
SPARK = 19

### PTS ###
TORCH_PT_1 = 31
TORCH_PT_2 = 32
TORCH_PT_3 = 33

vlv_channels = [f"gse_vlv_{i}" for i in [GOX_MPV, METHANE_MPV, SPARK]]
state_channels = [f"gse_state_{i}" for i in [GOX_MPV, METHANE_MPV, SPARK]]
pt_channels = [f"gse_pt_{i}_a" for i in [TORCH_PT_1, TORCH_PT_2, TORCH_PT_3]]
read_channels = state_channels + pt_channels
write_channels = vlv_channels

def attempt_light(auto):
    torch_pts = [auto[pt] for pt in pt_channels]
    return statistics.mean(torch_pts) > IGNITION_THRESHOLD

with client.control.acquire("igniter", read_channels, write_channels, 100) as auto:
    gox_mpv = syauto.Valve(auto, f"gse_vlv_{GOX_MPV}", f"gse_state_{GOX_MPV}")
    methane_mpv = syauto.Valve(auto, f"gse_vlv_{METHANE_MPV}", f"gse_state_{METHANE_MPV}")
    spark = syauto.Valve(auto, f"gse_vlv_{SPARK}", f"gse_state_{SPARK}")

    input("Press enter to start firing sequence ")

    try:
        METHANE = 0.089
        GOX = 0.961

        time.sleep(5 - SPARK_LEAD - GOX)
        spark.open()
        print("Sparking")
        time.sleep(SPARK_LEAD)

        print("Opening GOX MPV")
        gox_mpv.open()
        time.sleep(GOX - METHANE)

        print("Opening Methane MPV")
        methane_mpv.open()
        time.sleep(METHANE)

        # 0.089 methane
        # 0.961 ox

        ignition_start = time.time()
        auto.wait_until(lambda fun: attempt_light(auto), IGNITION_DURATION)
        
        if attempt_light(auto):
            print("Ignition successful")
            syauto.wait(round(IGNITION_DURATION - (time.time() - ignition_start), 2), False)
        else:
            print("Ignition failed")
        
        spark.close()
        gox_mpv.close()
        methane_mpv.close()
        print("Autosequence terminated")


    except KeyboardInterrupt:
        print("Aborting")
        gox_mpv.close()
        methane_mpv.close()
        spark.close()
        print("Aborted")