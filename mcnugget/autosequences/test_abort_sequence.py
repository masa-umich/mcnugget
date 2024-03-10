import time
# import keyboard
import synnax as sy
from synnax.control.controller import Controller
import syauto

# this connects to the synnax server for simulations
# this connects to the synnax simulation server
client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

# Connects to masa cluster
# client = sy.Synnax(
#     host="synnax.masa.engin.umich.edu",
#     port=80,
#     username="synnax",
#     password="seldon",
#     secure=True
# )

# valve names to channel names
v1_in = "gse_doa_1"
v1_out = "gse_doc_1"
v2_in = "gse_doa_2"
v2_out = "gse_doc_2"
v3_in = "gse_doa_3"
v3_out = "gse_doc_3"
v4_in = "gse_doa_4"
v4_out = "gse_doc_4"
v5_in = "gse_doa_5"
v5_out = "gse_doc_5"
v6_in = "gse_doa_6"
v6_out = "gse_doc_6"
v7_in = "gse_doa_7"
v7_out = "gse_doc_7"
v8_in = "gse_doa_8"
v8_out = "gse_doc_8"
v9_in = "gse_doa_9"
v9_out = "gse_doc_9"
v10_in = "gse_doa_10"
v10_out = "gse_doc_10"
v11_in = "gse_doa_11"
v11_out = "gse_doc_11"
v12_in = "gse_doa_12"
v12_out = "gse_doc_12"
v13_in = "gse_doa_13"
v13_out = "gse_doc_13"
v14_in = "gse_doa_14"
v14_out = "gse_doc_14"
v15_in = "gse_doa_15"
v15_out = "gse_doc_15"
v16_in = "gse_doa_16"
v16_out = "gse_doc_16"
v17_in = "gse_doa_17"
v17_out = "gse_doc_17"
v18_in = "gse_doa_18"
v18_out = "gse_doc_18"
v19_in = "gse_doa_19"
v19_out = "gse_doc_19"
v20_in = "gse_doa_20"
v20_out = "gse_doc_20"
v21_in = "gse_doa_21"
v21_out = "gse_doc_21"
v22_in = "gse_doa_22"
v22_out = "gse_doc_22"
v23_in = "gse_doa_23"
v23_out = "gse_doc_23"
v24_in = "gse_doa_24"
v24_out = "gse_doc_24"
# v25_in = "gse_doa_25"
# v25_out = "gse_doc_25"

# List of channels we're going to read from and write to
WRITE_TO = []
READ_FROM = []
for i in range(1, 25):
    WRITE_TO.append(f"gse_doc_{i}")
    READ_FROM.append(f"gse_doa_{i}")

start = sy.TimeStamp.now()

friendly_abort = False

print("starting autosequence")

with client.control.acquire(name="Press sequence",
                             write=WRITE_TO, read=READ_FROM, write_authorities=250 ) as auto:

    ###     THIS SECTION DECLARES THE VALVES WHICH WILL BE USED     ###
    #TODO: confirm that the specified channels are correct before running this autosequence

    # prevalves
    fuel_prevalve = syauto.Valve(
        auto=auto, cmd=v22_out, ack=v22_in, normally_open=False)
    ox_pre_valve = syauto.Valve(auto=auto, cmd=v21_out,
                                ack=v21_in, normally_open=False)
    
    # ISO valves
    fuel_press_ISO = syauto.Valve(
        auto=auto, cmd=v2_out, ack=v2_in,  normally_open=False)
    ox_press_ISO = syauto.Valve(auto=auto, cmd=v1_out,
                            ack=v1_in, normally_open=False)
    
    ox_dome_reg_pilot_iso =syauto.Valve(auto=auto, cmd = v5_out, ack = v5_in, normally_open=False)

    # vents
    fuel_vent = syauto.Valve(auto=auto, cmd=v15_out,
                             ack=v15_in, normally_open=True)
    press_vent = syauto.Valve(auto=auto, cmd=v18_out,
                              ack=v18_in, normally_open=True)
    ox_low_flow_vent = syauto.Valve(
        auto=auto, cmd=v16_out, ack=v16_in, normally_open=True)
    

    ###     THIS SECTION RUNS THE AUTOSEQUENCE AS FOLLOWS       ###
    ###      Aborts the autosequence as follows
    ##      1.  Closes all valves and vents

    syauto.close_all(auto,[ox_pre_valve,fuel_prevalve,ox_press_ISO,
                      fuel_press_ISO,ox_dome_reg_pilot_iso,
                      fuel_vent,press_vent,ox_low_flow_vent])
    