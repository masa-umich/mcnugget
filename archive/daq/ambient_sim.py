import time
import synnax
import random

client = synnax.Synnax()

sim_time = client.channels.create(
    name="main_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for i in range(1, 7):
    client.channels.create(
        name=f"gse_pt_{i}",
        data_type=synnax.DataType.FLOAT32,
        index=sim_time.key,
        retrieve_if_name_exists=True
    )

STATE = {}
READ_FROM = []
WRITE_TO = [
    "gse_pt_1", "gse_pt_2", "gse_pt_3", "gse_pt_4", "gse_pt_5", "gse_pt_6"
]

for pt in WRITE_TO:
    STATE[pt] = int(random.random() * 1000)

with client.open_writer(synnax.TimeStamp.now(), WRITE_TO) as writer:
    i = 0
    while True:
        if i % 50 == 0:
            print("simulating...")
        i += 1
        time.sleep(0.1)
        writer.write(STATE)
