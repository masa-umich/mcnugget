import time

import synnax as sy

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

DAQ_TIME = "daq_time"
TPC_CMD = "gse_doc_1"
TPC_ACK = "gse_doa_1"
MPV_CMD = "gse_doc_2"
MPV_ACK = "gse_doa_2"
PRESS_ISO_CMD = "gse_doc_3"
PRESS_ISO_ACK = "gse_doa_3"
# Normally open
VENT_CMD = "gse_doc_4"
VENT_ACK = "gse_doa_4"
SCUBA_PT = "gse_ai_1"
L_STAND_PT = "gse_ai_2"

daq_time = client.channels.create(
    name=DAQ_TIME,
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for i in range(1, 5):
    idx = client.channels.create(
        name=f"gse_doc_{i}_cmd_time",
        data_type=sy.DataType.TIMESTAMP,
        is_index=True,
        retrieve_if_name_exists=True
    )

    client.channels.create(
        [
            sy.Channel(
                name=f"gse_doc_{i}",
                data_type=sy.DataType.UINT8,
                index=idx.key
            ),
            sy.Channel(
                name=f"gse_doa_{i}",
                data_type=sy.DataType.FLOAT32,
                index=daq_time.key
            ),
        ],
        retrieve_if_name_exists=True,
    )

client.channels.create(
    name=SCUBA_PT,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

client.channels.create(
    name=L_STAND_PT,
    data_type=sy.DataType.FLOAT32,
    index=daq_time.key,
    retrieve_if_name_exists=True
)

rate = (sy.Rate.HZ * 20).period.seconds

DAQ_STATE = {
    # Valves
    TPC_CMD: 0,
    MPV_CMD: 0,
    PRESS_ISO_CMD: 0,
    VENT_CMD: 0,
    # Pts
    SCUBA_PT: 0,
    L_STAND_PT: 0,
}

MPV_LAST_OPEN = None
scuba_pressure = 0
l_stand_pressure = 0

with client.new_streamer([TPC_CMD, MPV_CMD, PRESS_ISO_CMD, VENT_CMD, ]) as streamer:
    with client.new_writer(
            sy.TimeStamp.now(),
            channels=[
                DAQ_TIME,
                TPC_ACK,
                MPV_ACK,
                PRESS_ISO_ACK,
                VENT_ACK,
                L_STAND_PT,
                SCUBA_PT,
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
                            print(k, f[k])
                            DAQ_STATE[k] = f[k][0]

                mpv_open = DAQ_STATE[MPV_CMD] == 1
                tpc_open = DAQ_STATE[TPC_CMD] == 1
                press_iso_open = DAQ_STATE[PRESS_ISO_CMD] == 1
                vent_open = DAQ_STATE[VENT_CMD] == 1

                if mpv_open and MPV_LAST_OPEN is None:
                    MPV_LAST_OPEN = sy.TimeStamp.now()
                elif not mpv_open:
                    MPV_LAST_OPEN = None

                l_stand_delta = 0
                scuba_delta = 0

                if press_iso_open:
                    scuba_delta += 2.5

                if tpc_open and scuba_pressure > 0 and not l_stand_pressure > scuba_pressure:
                    scuba_delta -= 1
                    l_stand_delta += 1

                if not vent_open:
                    l_stand_delta -= 1.5

                if not vent_open and tpc_open:
                    scuba_delta -= 1

                if mpv_open:
                    l_stand_delta -= 0.1 * sy.TimeSpan(sy.TimeStamp.now() - MPV_LAST_OPEN).seconds

                scuba_pressure += scuba_delta
                l_stand_pressure += l_stand_delta
                if scuba_pressure < 0:
                    scuba_pressure = 0
                if l_stand_pressure < 0:
                    l_stand_pressure = 0

                now = sy.TimeStamp.now()

                ok = w.write({
                    DAQ_TIME: now,
                    TPC_ACK: int(tpc_open),
                    MPV_ACK: int(mpv_open),
                    PRESS_ISO_ACK: int(press_iso_open),
                    VENT_ACK: int(vent_open),
                    SCUBA_PT: scuba_pressure,
                    L_STAND_PT: l_stand_pressure,
                })

                i += 1
                if (i % 40) == 0:
                    print(f"Committing {i} samples")
                    ok = w.commit()

            except Exception as e:
                print(e)
                raise e
