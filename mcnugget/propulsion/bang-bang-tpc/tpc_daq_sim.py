import time

import synnax as sy

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

TPC_VLV_1 = "tpc_vlv_1"
TPC_VLV_2 = "tpc_vlv_2"
MPV = "mpv"
PRESS_VLV = "press_vlv"
VENT_VLV = "vent_vlv"

DAQ_TIME = "daq_time"

daq_time = client.channels.create(
    name=DAQ_TIME,
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for valve in [TPC_VLV_1, TPC_VLV_2, MPV, PRESS_VLV, VENT_VLV]:
    idx = client.channels.create(
        name=f"{valve}_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True
    )

    client.channels.create(
        [
            sy.Channel(
                name=f"{valve}_cmd",
                data_type=sy.DataType.UINT8,
                index=idx.key
            ),
            sy.Channel(
                name=f"{valve}_ack",
                data_type=sy.DataType.FLOAT32,
                index=daq_time.key
            ),
        ],
        retrieve_if_name_exists=True,
    )

PT_CHANNEL = "pressure"

client.channels.create(
    name=PT_CHANNEL,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

rate = (sy.Rate.HZ * 20).period.seconds

DAQ_STATE = {
    "tpc_vlv_1_cmd": 0,
    "tpc_vlv_2_cmd": 0,
    "mpv_cmd": 0,
    "press_vlv_cmd": 0,
    "vent_vlv_cmd": 0,
}

pressure = 0
MPV_LAST_OPEN = None

with client.new_streamer([
    "tpc_vlv_1_cmd",
    "tpc_vlv_2_cmd",
    "mpv_cmd",
    "press_vlv_cmd",
    "vent_vlv_cmd"
]) as streamer:
    with client.new_writer(
            sy.TimeStamp.now(),
            channels=[
                "tpc_vlv_1_ack",
                "tpc_vlv_2_ack",
                "mpv_ack",
                "daq_time",
                "press_vlv_ack",
                "vent_vlv_ack",
                PT_CHANNEL,
            ]
    ) as w:
        i = 0
        while True:
            try:
                time.sleep(rate)
                if streamer.received:
                    while streamer.received:
                        f = streamer.read()
                        for k in f.columns:
                            DAQ_STATE[k] = f[k][0]

                mpv_open = DAQ_STATE["mpv_cmd"] == 1
                tpc_1_open = DAQ_STATE["tpc_vlv_1_cmd"] == 1
                tpc_2_open = DAQ_STATE["tpc_vlv_2_cmd"] == 1
                press_open = DAQ_STATE["press_vlv_cmd"] == 1
                vent_open = DAQ_STATE["vent_vlv_cmd"] == 1

                if mpv_open and MPV_LAST_OPEN is None:
                    MPV_LAST_OPEN = sy.TimeStamp.now()
                elif not mpv_open:
                    MPV_LAST_OPEN = None

                delta = 0

                if press_open:
                    delta += 1

                if vent_open:
                    delta -= 5

                if mpv_open:
                    delta -= 0.5 * sy.TimeSpan(sy.TimeStamp.now() - MPV_LAST_OPEN).seconds

                if tpc_1_open:
                    delta += 3

                if tpc_2_open:
                    delta += 3

                if pressure + delta < 0:
                    delta = 0

                pressure += delta

                now = sy.TimeStamp.now()
                ok = w.write({
                    "tpc_vlv_1_ack": DAQ_STATE["tpc_vlv_1_cmd"],
                    "tpc_vlv_2_ack": DAQ_STATE["tpc_vlv_2_cmd"],
                    "mpv_ack": DAQ_STATE["mpv_cmd"],
                    "daq_time": now,
                    "press_vlv_ack": DAQ_STATE["press_vlv_cmd"],
                    "vent_vlv_ack": DAQ_STATE["vent_vlv_cmd"],
                    PT_CHANNEL: pressure
                })

                i += 1
                if (i % 100) == 0:
                    print(f"Committing {i} samples")
                    ok = w.commit()

            except Exception as e:
                print(e)
                raise e
