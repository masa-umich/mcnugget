import time
import random
import synnax as sy
import websockets
import math
import sys

args = sys.argv[1:]
_NOISE = "noise" in args
_NEW_CHANNELS = "new_channels" in args
_LEAKS = "leaks" in args

try:
    client = sy.Synnax(
        host="localhost", port=9090, username="synnax", password="seldon", secure=False
    )
except:
    print("unable to connect to cluster - is it running?")
    exit(0)

GSE_TIME = "gse_time"
RATE = (sy.Rate.HZ * 100).period.seconds

VALVES = {
    "OX_RETURN_LINE": 1,
    "OX_FILL": 2,
    "OX_PREVALVE": 3,
    "OX_DRAIN": 4,
    "MARGIN": 5,
    "FUEL_PRE_PRESS": 6,
    "OX_PRE_PRESS": 7,
    "MPV_PURGE": 8,
    "BROKEN_1": 9,
    "BROKEN_2": 10,
    "OX_MPV": 19,
    "FUEL_MPV": 12,
    "BROKEN_3": 13,
    "GOX_PILOT": 14,
    "METHANE_PILOT": 15,
    "METHANE_MPV": 16,
    "FUEL_PREVALVE": 17,
    "IGNITER": 18,
    "K2_PRESS_ISO": 20,
    "FUEL_DOME_ISO": 21,
    "OX_DOME_ISO": 22,
    "OX_VENT": 23,
    "FUEL_VENT": 24,
}

PTS = {
    "PRESS_BOTTLES": 4,
    "OX_TPC_OUTLET": 8,
    "OX_FLOWMETER_INLET": 9,
    "OX_FLOWMETER_THROAT": 10,
    "FUEL_FLOWMETER_INLET": 12,
    "FUEL_FLOWMETER_THROAT": 13,
    "FUEL_TPC_OUTLET": 18,
    "FUEL_1": 19,
    "FUEL_2": 20,
    "FUEL_3": 21,
    "CHAMBER_1": 22,
    "CHAMBER_2": 23,
    "METHANE_BOTTLE": 26,
    "GOX_BOTTLE": 28,
    "TORCH_1": 31,
    "TORCH_2": 32,
    "TORCH_3": 33,
    "PURGE": 34,
    "OX_1": 39,
    "OX_2": 40,
    "OX_3": 41,
}

TCS = {
    "OX_FLOWMETER": 5
}

LOCAL = {}
REMOTE = {}
STATE = {}

# for channel, index in VALVES.items():
for index in range(24):
    LOCAL[f"gse_state_{index + 1}"] = 0
    REMOTE[f"gse_vlv_{index + 1}"] = 0

for channel, index in PTS.items():
    LOCAL[f"gse_pt_{index}_avg"] = 0

for channel, index in TCS.items():
    LOCAL[f"gse_tc_{index}"] = 0

if _NEW_CHANNELS:
    gse_time = client.channels.create(
        name=GSE_TIME, 
        data_type=sy.DataType.TIMESTAMP,
        is_index=True, 
        retrieve_if_name_exists=True
    )
    print("creating channel gse_time")

    for channel in LOCAL.keys():
        print(f"creating channel {channel}")
        client.channels.create(
            name=channel,
            data_type=sy.DataType.UINT8 if "state" in channel else sy.DataType.FLOAT32,
            index=gse_time.key,
            retrieve_if_name_exists=True
        )

    for channel in REMOTE.keys():
        print(f"creating channel {channel}")
        client.channels.create(
            name=channel,
            data_type=sy.DataType.UINT8,
            virtual=True,
            retrieve_if_name_exists=True
        )

gse_time = client.channels.retrieve(GSE_TIME)
# client.channels.create(
#     name="ox_mixage",
#     data_type=sy.DataType.FLOAT32,
#     index=gse_time.key,
#     retrieve_if_name_exists=True
# )
# LOCAL["ox_mixage"] = 0

try:
    chan = GSE_TIME
    client.channels.retrieve(GSE_TIME)
    for channel in LOCAL.keys():
        chan = channel
        client.channels.retrieve(channel)
    for channel in REMOTE.keys():
        chan = channel
        client.channels.retrieve(channel)
    print(f"retrieved all channels")
except sy.exceptions.NotFoundError:
    print(f"error: could not retrieve channel {chan} - if running on a fresh cluster, please specify the `new_channels` argument")
    exit(0)

errors = 0
iteration = 0

STATE["press_bottles"] = 2000
STATE["purge_bottle"] = 2000
STATE["fuel_tanks"] = 0
STATE["ox_tanks"] = 0
# STATE["fuel_mixage"] = 0
# STATE["ox_mixage"] = 0
STATE["ox_flowmeter_inlet"] = 0
STATE["ox_flowmeter_throat"] = 0
STATE["fuel_flowmeter_inlet"] = 0
STATE["fuel_flowmeter_throat"] = 0
STATE["ox_tpc_outlet"] = 0
STATE["fuel_tpc_outlet"] = 0

STATE["ox_reg_set_pressure"] = 390
STATE["fuel_reg_set_pressure"] = 400

REMOTE[f"gse_vlv_{VALVES['OX_VENT']}"] = 1
REMOTE[f"gse_vlv_{VALVES['FUEL_VENT']}"] = 1
REMOTE[f"gse_vlv_{VALVES['OX_MPV']}"] = 1
REMOTE[f"gse_vlv_{VALVES['FUEL_MPV']}"] = 1

print(f"reading from {len(list(REMOTE.keys()))} channels")
print(f"writing to {len(list(LOCAL.keys()))} channels")
print(f"rate: {RATE} seconds")
with client.open_streamer(list(REMOTE.keys())) as streamer:
    with client.open_writer(
        sy.TimeStamp.now(),
        channels=list(LOCAL.keys()) + [GSE_TIME],
        name="coldflow_sim",
        enable_auto_commit=True,
    ) as writer:
        while True:
            try:
                time.sleep(RATE)
                while True:
                    f = streamer.read(0)
                    if f is None:
                        break
                    for c in f.channels:
                        REMOTE[c] = int(f[c][-1])
            
                for channel, state in REMOTE.items():
                    LOCAL[channel.replace("vlv", "state")] = state

                STATE["press_iso"] = LOCAL[f"gse_state_{VALVES['K2_PRESS_ISO']}"]
                STATE["ox_prepress"] = LOCAL[f"gse_state_{VALVES['OX_PRE_PRESS']}"]
                STATE["fuel_prepress"] = LOCAL[f"gse_state_{VALVES['FUEL_PRE_PRESS']}"]
                STATE["ox_dome_iso"] = LOCAL[f"gse_state_{VALVES['OX_DOME_ISO']}"]
                STATE["fuel_dome_iso"] = LOCAL[f"gse_state_{VALVES['FUEL_DOME_ISO']}"]
                STATE["ox_vent"] = LOCAL[f"gse_state_{VALVES['OX_VENT']}"]
                STATE["fuel_vent"] = LOCAL[f"gse_state_{VALVES['FUEL_VENT']}"]
                STATE["ox_prevalve"] = LOCAL[f"gse_state_{VALVES['OX_PREVALVE']}"]
                STATE["fuel_prevalve"] = LOCAL[f"gse_state_{VALVES['FUEL_PREVALVE']}"]
                STATE["ox_mpv"] = LOCAL[f"gse_state_{VALVES['OX_MPV']}"]
                STATE["fuel_mpv"] = LOCAL[f"gse_state_{VALVES['FUEL_MPV']}"]

                if STATE["ox_prepress"] == 1 and STATE["purge_bottle"] > STATE["ox_tanks"]:
                    if STATE["ox_tanks"] < 700:
                        coeff = math.sqrt(abs(STATE["purge_bottle"] - STATE["ox_tanks"]))
                        STATE["ox_tanks"] += 9 * RATE * coeff
                        STATE["purge_bottle"] -= 8 * RATE * coeff

                if STATE["fuel_prepress"] == 1 and STATE["purge_bottle"] > STATE["fuel_tanks"]:
                    if STATE["fuel_tanks"] < 700:
                        coeff = math.sqrt(abs(STATE["purge_bottle"] - STATE["fuel_tanks"]))
                        # STATE["fuel_tanks"] += 4 * RATE * coeff
                        STATE["fuel_tanks"] += 1 * RATE * coeff
                        STATE["purge_bottle"] -= 8 * RATE * coeff

                if STATE["press_iso"] == 1:
                    if STATE["fuel_dome_iso"] == 1:
                        STATE["fuel_tpc_outlet"] = min(STATE["fuel_reg_set_pressure"], STATE["press_bottles"])
                        coeff = math.sqrt(abs(STATE["press_bottles"] - STATE["fuel_tanks"]))
                        # if STATE["fuel_tpc_outlet"] > STATE["fuel_tanks"]:
                        if STATE["press_bottles"] > STATE["fuel_tanks"]:
                            STATE["fuel_tanks"] += 2 * RATE * coeff
                            STATE["press_bottles"] -= 1 * RATE * coeff

                        # STATE["fuel_mixage"] += RATE / 1.8
                        # if STATE["fuel_mixage"] < 0.15:
                        #     STATE["fuel_tanks"] -= 1.2 * RATE * coeff
                        # elif STATE["fuel_mixage"] < 0.5:
                        #     STATE["fuel_tanks"] -= 5.8 * RATE * coeff
                        # elif STATE["fuel_mixage"] < 1:
                        #     STATE["fuel_tanks"] -= 1.4 * RATE * coeff
                        # else:
                        #     # STATE["fuel_tanks"] -= 0.1 * RATE * coeff
                        #     pass

                        # LOCAL["ox_mixage"] = STATE["fuel_mixage"]

                    if STATE["ox_dome_iso"] == 1:
                        STATE["ox_tpc_outlet"] = min(STATE["ox_reg_set_pressure"], STATE["press_bottles"])
                        coeff = math.sqrt(abs(STATE["press_bottles"] - STATE["ox_tanks"]))
                        if STATE["ox_tpc_outlet"] > STATE["ox_tanks"]:
                            STATE["ox_tanks"] += 4 * RATE * coeff
                            STATE["press_bottles"] -= 1 * RATE * coeff
                            
                        # STATE["ox_mixage"] += RATE / 1.8
                        # if STATE["ox_mixage"] < 0.15:
                        #     STATE["ox_tanks"] -= 1.3 * RATE * coeff
                        # elif STATE["ox_mixage"] < 0.4:
                        #     STATE["ox_tanks"] -= 6.2 * RATE * coeff
                        # elif STATE["ox_mixage"] < 1:
                        #     STATE["ox_tanks"] -= 1.4 * RATE * coeff
                        # else:
                        #     # STATE["ox_tanks"] -= 0.1 * RATE * coeff
                        #     pass

                if STATE["ox_vent"] == 0:
                    coeff = math.sqrt(abs(STATE["ox_tanks"]))
                    STATE["ox_tanks"] -= 60 * RATE * coeff

                if STATE["fuel_vent"] == 0:
                    coeff = math.sqrt(abs(STATE["fuel_tanks"]))
                    STATE["fuel_tanks"] -= 60 * RATE * coeff

                if STATE["ox_prevalve"] == 1 and STATE["ox_mpv"] == 0:
                    coeff = math.sqrt(abs(STATE["ox_tanks"]))
                    # STATE["ox_tanks"] -= 3 * RATE * coeff
                    STATE["ox_tanks"] -= 5.9 * (1.5) * RATE * coeff

                if STATE["fuel_prevalve"] == 1 and STATE["fuel_mpv"] == 0:
                    coeff = math.sqrt(abs(STATE["fuel_tanks"]))
                    # STATE["fuel_tanks"] -= 3 * RATE * coeff
                    STATE["fuel_tanks"] -= 5.8 * (1.5) * RATE * coeff
                
                for pressure in ["ox_tpc_outlet", "fuel_tpc_outlet", "ox_flowmeter_inlet", "ox_flowmeter_throat", "fuel_flowmeter_inlet", "fuel_flowmeter_throat", "ox_tanks", "fuel_tanks", "press_bottles", "purge_bottle"]:
                    if STATE[pressure] < 0:
                        STATE[pressure] = 0
                
                # for mixage in ["ox_mixage", "fuel_mixage"]:
                #     if STATE[mixage] > 1:
                #         STATE[mixage] = 1
                #     if STATE[mixage] < 0:
                #         STATE[mixage] = 0

                STATE["ox_flowmeter_inlet"] = STATE["ox_tanks"]
                STATE["ox_flowmeter_throat"] = max(STATE["ox_tanks"] - 50, 0)
                STATE["fuel_flowmeter_inlet"] = STATE["fuel_tanks"]
                STATE["fuel_flowmeter_throat"] = max(STATE["fuel_tanks"] - 55, 0)

                STATE["ox_flowmeter_tc"] = -200   # celsius
                
                if _LEAKS:
                    for pressure in ["fuel_tanks", "ox_tanks"]:
                        coeff = math.sqrt(abs(STATE[pressure]))
                        STATE[pressure] -= 0.5 * RATE * coeff
                    for pressure in ["press_bottles", "purge_bottle"]:
                        coeff = math.sqrt(abs(STATE[pressure]))
                        STATE[pressure] -= 0.02 * RATE * coeff
                    for pressure in ["ox_flowmeter_inlet", "ox_flowmeter_throat", "fuel_flowmeter_inlet", "fuel_flowmeter_throat"]:
                        coeff = math.sqrt(abs(STATE[pressure]))
                        STATE[pressure] -= 5 * RATE * coeff
                    for pressure in ["ox_tpc_outlet", "fuel_tpc_outlet"]:
                        coeff = math.sqrt(abs(STATE[pressure]))
                        STATE[pressure] -= 10 * RATE * coeff

                # put values into LOCAL
                LOCAL[f"gse_tc_{TCS['OX_FLOWMETER']}"] = STATE["ox_flowmeter_tc"]
                LOCAL[f"gse_pt_{PTS['PRESS_BOTTLES']}_avg"] = STATE["press_bottles"]
                LOCAL[f"gse_pt_{PTS['OX_TPC_OUTLET']}_avg"] = STATE["ox_tpc_outlet"]
                LOCAL[f"gse_pt_{PTS['FUEL_TPC_OUTLET']}_avg"] = STATE["fuel_tpc_outlet"]
                LOCAL[f"gse_pt_{PTS['OX_FLOWMETER_INLET']}_avg"] = STATE["ox_flowmeter_inlet"]
                LOCAL[f"gse_pt_{PTS['OX_FLOWMETER_THROAT']}_avg"] = STATE["ox_flowmeter_throat"]
                LOCAL[f"gse_pt_{PTS['FUEL_FLOWMETER_INLET']}_avg"] = STATE["fuel_flowmeter_inlet"]
                LOCAL[f"gse_pt_{PTS['FUEL_FLOWMETER_THROAT']}_avg"] = STATE["fuel_flowmeter_throat"]
                LOCAL[f"gse_pt_{PTS['FUEL_1']}_avg"] = STATE["fuel_tanks"]
                LOCAL[f"gse_pt_{PTS['FUEL_2']}_avg"] = STATE["fuel_tanks"]
                LOCAL[f"gse_pt_{PTS['FUEL_3']}_avg"] = STATE["fuel_tanks"]
                LOCAL[f"gse_pt_{PTS['CHAMBER_1']}_avg"] = 0
                LOCAL[f"gse_pt_{PTS['CHAMBER_2']}_avg"] = 0
                LOCAL[f"gse_pt_{PTS['METHANE_BOTTLE']}_avg"] = 0
                LOCAL[f"gse_pt_{PTS['GOX_BOTTLE']}_avg"] = 0
                LOCAL[f"gse_pt_{PTS['TORCH_1']}_avg"] = 0
                LOCAL[f"gse_pt_{PTS['TORCH_2']}_avg"] = 0
                LOCAL[f"gse_pt_{PTS['TORCH_3']}_avg"] = 0
                LOCAL[f"gse_pt_{PTS['PURGE']}_avg"] = STATE["purge_bottle"]
                LOCAL[f"gse_pt_{PTS['OX_1']}_avg"] = STATE["ox_tanks"]
                LOCAL[f"gse_pt_{PTS['OX_2']}_avg"] = STATE["ox_tanks"]
                LOCAL[f"gse_pt_{PTS['OX_3']}_avg"] = STATE["ox_tanks"]
                if _NOISE:
                    for pt in [PTS['PRESS_BOTTLES'], PTS['OX_TPC_OUTLET'], PTS['FUEL_TPC_OUTLET'], PTS['PURGE']]:
                        LOCAL[f"gse_pt_{pt}_avg"] = random.normalvariate(LOCAL[f"gse_pt_{pt}_avg"], 10)
                    for pt in [PTS['OX_1'], PTS['OX_2'], PTS['OX_3'], PTS['FUEL_1'], PTS['FUEL_2'], PTS['FUEL_3']]:
                        LOCAL[f"gse_pt_{pt}_avg"] = random.normalvariate(LOCAL[f"gse_pt_{pt}_avg"], 4)
                    for pt in [PTS['OX_FLOWMETER_INLET'], PTS['OX_FLOWMETER_THROAT'], PTS['FUEL_FLOWMETER_INLET'], PTS['FUEL_FLOWMETER_THROAT']]:
                        LOCAL[f"gse_pt_{pt}_avg"] = random.normalvariate(LOCAL[f"gse_pt_{pt}_avg"], 4)
                    for tc in [TCS['OX_FLOWMETER']]:
                        LOCAL[f"gse_tc_{tc}"] = random.normalvariate(LOCAL[f"gse_tc_{tc}"], 2)
                LOCAL[GSE_TIME] = sy.TimeStamp.now()
                
                # print(LOCAL)
                writer.write(LOCAL)
                
                if iteration % 6000 == 0:
                    print("iteration ", iteration)
                iteration += 1

            except KeyboardInterrupt:
                print("\nterminating sim")
                break

            except Exception as e:
                print(f"error: {e}")
                errors += 1
                if errors >= 5:
                    print("allowable errors exceeded, terminating sim")
                    break
                continue

            except websockets.exceptions.ConnectionClosedError:
                print("lost connection to cluster, terminating sim")
                break
        