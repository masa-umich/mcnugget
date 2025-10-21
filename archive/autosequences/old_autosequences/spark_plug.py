import synnax
import time

client = synnax.Synnax()

spark_plug_1 = client.channels.retrieve("gse_vlv_7")
spark_plug_2 = client.channels.retrieve("gse_vlv_8")

gse_state_time = client.channels.retrieve("gse_state_time")

spark_plug_command = client.channels.create(
    name="spark_plug_command",
    data_type=synnax.DataType.UINT8,
    virtual=True,
    retrieve_if_name_exists=True,
)
spark_plug_state = client.channels.create(
    name="spark_plug_state",
    data_type=synnax.DataType.UINT8,
    index=gse_state_time.key,
    retrieve_if_name_exists=True,
)

i = 0
spark_command = 0
WRITE_STATE = {}

# with client.control.acquire(name="spark plug shenanigans", read=["spark_plug_command"], write=["gse_vlv_7", "gse_vlv_8"], write_authorities=20) as auto:
with client.open_streamer(["spark_plug_command"]) as streamer:
    with client.open_writer(synnax.TimeStamp.now(), ["gse_vlv_7", "gse_vlv_8", "spark_plug_state", "spark_plug_time"]) as writer:
        time.sleep(2)
        while True:
            frame = streamer.read(0)
            if frame is not None:
                spark_command = frame["spark_plug_command"]

            if spark_command == 1:
                WRITE_STATE = {
                    "gse_vlv_7": 1,
                    "gse_vlv_8": 1,
                    "spark_plug_state": 1
                }
            elif spark_command == 0:
                WRITE_STATE = {
                    "gse_vlv_7": 0,
                    "gse_vlv_8": 0,
                    "spark_plug_state": 0
                }
            else:
                time.sleep(0.01)

            i += 1
            if i % 500 == 0:
                print("waiting for spark command")
            writer.write(WRITE_STATE)