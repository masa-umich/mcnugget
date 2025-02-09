import synnax
import time

client = synnax.Synnax()

spark_plug_1 = client.channels.retrieve("gse_do_4_6_cmd")
spark_plug_2 = client.channels.retrieve("gse_do_4_5_cmd")

with client.control.acquire("spark", read=[], write=["gse_do_4_6_cmd", "gse_do_4_5_cmd"], write_authorities=20) as auto:
    time.sleep(1)
    print("energizing channels")
    auto.set({
        "gse_do_4_6_cmd": 1,
        "gse_do_4_5_cmd": 1
    })
    time.sleep(5)
    auto.set({
        "gse_do_4_6_cmd": 0,
        "gse_do_4_5_cmd": 0
    })
    print("deenergizing channels")

time.sleep(1)