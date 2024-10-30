"""
This is a basic simulation intended only for the simulation of the Press Fill autosequence.

It mirrors the changes described in the Coldflow SOP here as of ** March 9, 2024 **:
https://docs.google.com/spreadsheets/d/1irVQy6_5JwPJJ3sweFRS64LlDM8QSsG3xSU4e92X_aM/edit#gid=631819219


### VALVES

gse_doa_3 (Air Drive ISO 1)
gse_doa_4 (Air Drive ISO 2)
gse_doa_20 (Gas Drive Booster)
gse_doa_23 (Press Fill)
gse_doa_18 (Press Vent)

The Sim also writes to the corresponding doc channels


### PTs

These 3 are for the Press Tanks
gse_ai_22
gse_ai_24
gse_ai_26

Press Supply Tank
gse_ai_23


### TCs

All 4 of these are for the Press Tanks
gse_tc_5 = gse_ai_70
gse_tc_6 = gse_ai_71
gse_tc_7 = gse_ai_72
gse_tc_8 = gse_ai_73


"""

import time
import sys
sys.path.append("/opt/homebrew/lib/python3.11/site-packages")
import synnax as sy

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

DAQ_TIME = "daq_time"


daq_time = client.channels.create(
    name=DAQ_TIME,
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True
)

for i in range(1, 25):
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

for i in range(1, 38):
    client.channels.create(
        name=f"gse_ai_{i}",
        data_type=sy.DataType.FLOAT32,
        index=daq_time.key,
        retrieve_if_name_exists=True
    )

for i in range(65, )

rate = (sy.Rate.HZ * 50).period.seconds

DAQ_STATE = {
    # Valves
    TPC_1_OPEN_CMD: 0,
    TPC_2_OPEN_CMD: 0,
    TPC_1_CLOSE_CMD: 1,
    TPC_2_CLOSE_CMD: 1,
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

with client.new_streamer([TPC_1_OPEN_CMD, TPC_2_OPEN_CMD, TPC_1_CLOSE_CMD, TPC_2_CLOSE_CMD, MPV_CMD, PRESS_ISO_CMD, VENT_CMD, ]) as streamer:
    with client.new_writer(
            sy.TimeStamp.now(),
            channels=[
                DAQ_TIME,
                TPC_1_OPEN_ACK,
                TPC_2_OPEN_ACK,
                TPC_1_CLOSE_ACK,
                TPC_2_CLOSE_ACK,
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
                            DAQ_STATE[k] = f[k][0]

                mpv_open = DAQ_STATE[MPV_CMD] == 1
                tpc_1_open = DAQ_STATE[TPC_1_OPEN_CMD] == 1
                tpc_1_close = DAQ_STATE[TPC_1_CLOSE_CMD] == 1
                tpc_2_open = DAQ_STATE[TPC_2_OPEN_CMD] == 1
                tpc_2_close = DAQ_STATE[TPC_2_CLOSE_CMD] == 1
                # if (tpc_1_open == tpc_1_close) or (tpc_2_open == tpc_2_close):
                #     raise Exception("Dual solenoid both open or both closed")
                press_iso_open = DAQ_STATE[PRESS_ISO_CMD] == 1
                vent_open = DAQ_STATE[VENT_CMD] == 0

                if mpv_open and MPV_LAST_OPEN is None:
                    MPV_LAST_OPEN = sy.TimeStamp.now()
                elif not mpv_open:
                    MPV_LAST_OPEN = None

                l_stand_delta = 0
                scuba_delta = 0

                if press_iso_open:
                    scuba_delta += 2.5

                if tpc_1_open and scuba_pressure > 0 and not l_stand_pressure > scuba_pressure:
                    scuba_delta -= 1
                    l_stand_delta += 1

                if tpc_2_open and scuba_pressure > 0 and not l_stand_pressure > scuba_pressure:
                    scuba_delta -= 1
                    l_stand_delta += 1

                if vent_open:
                    l_stand_delta -= 1.5

                if vent_open and tpc_1_open:
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
                    TPC_1_OPEN_ACK: int(tpc_1_open),
                    TPC_2_OPEN_ACK: int(tpc_2_open),
                    TPC_1_CLOSE_ACK: int(tpc_1_close),
                    TPC_2_CLOSE_ACK: int(tpc_2_close),
                    MPV_ACK: int(mpv_open),
                    PRESS_ISO_ACK: int(press_iso_open),
                    VENT_ACK: not int(vent_open),
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