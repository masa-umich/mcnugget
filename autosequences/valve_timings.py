import synnax
import syauto
import time

client = synnax.Synnax(
    host="141.212.192.160",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False,
)
# client = synnax.Synnax(
#     host="localhost",
#     port=9090,
#     username="synnax",
#     password="seldon",
#     secure=False,
# )

OX_VLV = "gse_vlv_19"
OX_STATE = "gse_state_19"

FUEL_VLV = "gse_vlv_12"
FUEL_STATE = "gse_state_12"

with client.control.acquire("valve timings", [OX_STATE, FUEL_STATE], [OX_VLV, FUEL_VLV]) as auto:
    ox_mpv = syauto.Valve(
        auto=auto,
        cmd=OX_VLV,
        ack=OX_STATE,
        normally_open=True
    )
    fuel_mpv = syauto.Valve(
        auto=auto,
        cmd=FUEL_VLV,
        ack=FUEL_STATE,
        normally_open=True
    )

    input("Press enter to start: ")

    fuel_mpv.open()

    time.sleep(0.25)

    ox_mpv.open()

    time.sleep(0.5)

    ox_mpv.close()
    fuel_mpv.close()

    print("completed")
    
    time.sleep(0.5)