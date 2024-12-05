import time
import synnax

client = synnax.Synnax()

main_time = client.channels.create(
    name="main_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

ox_mpv_cmd_time = client.channels.create(
    name="ox_mpv_cmd_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
ox_mpv_cmd = client.channels.create(
    name="ox_mpv_cmd",
    data_type=synnax.DataType.UINT8,
    index=ox_mpv_cmd_time.key,
    retrieve_if_name_exists=True
)
ox_mpv_state = client.channels.create(
    name="ox_mpv_state",
    data_type=synnax.DataType.UINT8,
    index=main_time.key,
    retrieve_if_name_exists=True
)
fuel_mpv_cmd_time = client.channels.create(
    name="fuel_mpv_cmd_time",
    data_type=synnax.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)
fuel_mpv_cmd = client.channels.create(
    name="fuel_mpv_cmd",
    data_type=synnax.DataType.UINT8,
    index=fuel_mpv_cmd_time.key,
    retrieve_if_name_exists=True
)
fuel_mpv_state = client.channels.create(
    name="fuel_mpv_state",
    data_type=synnax.DataType.UINT8,
    index=main_time.key,
    retrieve_if_name_exists=True
)
fuel_tank = client.channels.create(
    name="fuel_tank",
    data_type=synnax.DataType.FLOAT32,
    index=main_time.key,
    retrieve_if_name_exists=True
)
ox_tank = client.channels.create(
    name="ox_tank",
    data_type=synnax.DataType.FLOAT32,
    index=main_time.key,
    retrieve_if_name_exists=True
)
thrust = client.channels.create(
    name="thrust",
    data_type=synnax.DataType.FLOAT32,
    index=main_time.key,
    retrieve_if_name_exists=True
)

READ_FROM = [
    "fuel_mpv_cmd", "ox_mpv_cmd"
]

WRITE_TO = [
    "ox_tank", "fuel_tank", "thrust", "ox_mpv_state", "fuel_mpv_state", "main_time"
]

ox_tank = 8000
fuel_tank = 6000
thrust = 0
ox_mpv_open = False
fuel_mpv_open = False

STATE = {}

# with client.control.acquire(name="rocket_sim", read=READ_FROM, write=WRITE_TO, write_authorities=255) as auto:
with client.open_writer(synnax.TimeStamp.now(), WRITE_TO) as writer:
    with client.open_streamer(READ_FROM) as streamer:
        while True:
            time.sleep(0.025)
            print("hi im running")

            # read values
            frame = streamer.read(0.01)
            if frame:
                for key, value in frame.items():
                    if key == "ox_mpv_cmd":
                        ox_mpv_open = value == 1
                    elif key == "fuel_mpv_cmd":
                        fuel_mpv_open = value == 1
            
            if ox_mpv_open:
                ox_tank -= 2
                thrust += 2
            
            if fuel_mpv_open:
                fuel_tank -= 3
                thrust += 3
            
            if ox_mpv_open and fuel_mpv_open:
                thrust += 5
            
            thrust -= 0.2

            # write values
            STATE["ox_tank"] = ox_tank
            STATE["fuel_tank"] = fuel_tank
            STATE["thrust"] = thrust
            STATE["ox_mpv_state"] = ox_mpv_open
            STATE["fuel_mpv_state"] = fuel_mpv_open
            STATE["main_time"] = synnax.TimeStamp.now()

            writer.write(STATE)