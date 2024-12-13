from synnax.control.controller import Controller
from autosequences import syauto
import time
import synnax as sy
import statistics

NITROUS_MPV_DOC = "torch_state_0"
NITROUS_MPV_DOA = "torch_vlv_0"

ETHANOL_MPV_DOC = "torch_state_1"
ETHANOL_MPV_DOA = "torch_vlv_1"

TORCH_ISO_DOC = "torch_state_2"
TORCH_ISO_DOA = "torch_vlv_2"

TORCH_PURGE_DOC = "torch_state_4"
TORCH_PURGE_DOA = "torch_vlv_4"

ETHANOL_TANK_VENT_DOC = "torch_state_3"
ETHANOL_TANK_VENT_DOA = "torch_vlv_3"

SPARK_PLUG_DOC = "torch_state_5"
SPARK_PLUG_DOA = "torch_vlv_5"

TORCH_PT_TARGET = 620

PRESS_RATE = 50

DURATION_BEFORE_SPARK = 0.19

SECONDS_OF_SPARKING = 3

SPARK_RATE = 25

ETHANOL_TANK_PT = "ethanol_pt_5"

NITROUS_TANK_PT = "nitrous_pt_1"

TORCH_PT_1 = "torch_pt_6"
TORCH_PT_2 = "torch_pt_7"
TORCH_PT_3 = "torch_pt_8"

client = sy.Synnax()

CMDS = [NITROUS_MPV_DOC,ETHANOL_MPV_DOC,TORCH_ISO_DOC,TORCH_PURGE_DOC,ETHANOL_TANK_VENT_DOC,SPARK_PLUG_DOC]
ACKS = [NITROUS_MPV_DOA,ETHANOL_MPV_DOA,TORCH_ISO_DOA,TORCH_PURGE_DOA,ETHANOL_TANK_VENT_DOA,ETHANOL_TANK_VENT_DOA]
PTS = [ETHANOL_TANK_PT,NITROUS_TANK_PT,TORCH_PT_1,TORCH_PT_2,TORCH_PT_3]

WRITE_TO = []
READ_FROM = []

for cmd in CMDS:
    WRITE_TO.append(cmd)

for ack in ACKS:
    READ_FROM.append(ack)

for pt in PTS:
    READ_FROM.append(pt)


# def ethanol_press():
#     return auto[ETHANOL_TANK_PT] >= ETHANOL_PRESS_TARGET

auto = client.control.acquire(name="Torch Ignition Booyah", write=WRITE_TO, read=READ_FROM, write_authorities=222)

nitrous_mpv = syauto.Valve(auto=auto, cmd=NITROUS_MPV_DOC, ack=NITROUS_MPV_DOA, normally_open=True)

ethanol_mpv = syauto.Valve(auto=auto, cmd=ETHANOL_MPV_DOC, ack=ETHANOL_MPV_DOA, normally_open=True)

torch_iso = syauto.Valve(auto=auto, cmd=TORCH_ISO_DOC, ack=TORCH_ISO_DOA, normally_open=False)

torch_purge = syauto.Valve(auto=auto, cmd=TORCH_PURGE_DOC, ack=TORCH_PURGE_DOA, normally_open=False)

ethanol_tank_vent = syauto.Valve(auto=auto, cmd=ETHANOL_TANK_VENT_DOC, ack=ETHANOL_TANK_VENT_DOA, normally_open=True)

spark_plug = syauto.Valve(auto=auto, cmd=SPARK_PLUG_DOC, ack=SPARK_PLUG_DOA, normally_open=False)

try:
    ans = input("Type 'start' to commence autosequence. ")
    if not (ans == 'start' or ans == 'Start' or ans == 'START'):
        exit()

    print("Starting Igniter Autosequence. Setting initial system state.")
    syauto.close_all(auto, [nitrous_mpv, ethanol_mpv, torch_iso, torch_purge, ethanol_tank_vent])
    time.sleep(1)

    torch_iso.open()

    retry = True
    while(retry == True):
        print("opening ethanol mpv")
        ethanol_mpv.open()

        time.sleep(.01)

        print("opening nitrous mpv")
        nitrous_mpv.open()

        time.sleep(DURATION_BEFORE_SPARK)

        start = sy.TimeStamp.now();
        torch_ignited = False
        while(sy.TimeStamp.now() - start < 3 and torch_ignited == False):
            for j in range(SPARK_RATE):
                spark_plug.open()
                spark_plug.close()
                pts_median = statistics.median(auto[TORCH_PT_1],auto[TORCH_PT_2],auto[TORCH_PT_3])
                if(pts_median >= TORCH_PT_TARGET):
                    torch_ignited = True
                    retry = False
                    break
                else:
                    time.sleep(.04)

        
        if(torch_ignited == False):
            syauto.close_all(auto, [nitrous_mpv,ethanol_mpv])
            torch_purge.open()
            time.sleep(2)
            torch_purge.close()
            print(f"Ethanol Supply: {auto[ETHANOL_TANK_PT]} psig")
            print(f"Nitrous Supply: {auto[NITROUS_TANK_PT]} psig")
            testAgain = input("Type 'retry' to retry autosequence. ")
            if testAgain != 'retry' or testAgain != 'Retry':
                retry = False

except KeyboardInterrupt as e:
    print("Manual abort, safing system")
    print("Closing all valves and vents")
    syauto.open_close_many_valves(auto=auto, valves_to_open=[ethanol_tank_vent], valves_to_close=[ethanol_mpv, nitrous_mpv, torch_iso])
    
    torch_purge.open()
    time.sleep(2)
    torch_purge.close()

    auto.release()
    print("terminated")

time.sleep(2)
syauto.close_all(auto, [nitrous_mpv,ethanol_mpv])
print("Terminating Autosequence")
print("Closing all valves and vents")
syauto.open_close_many_valves(auto=auto, valves_to_open=[ethanol_tank_vent], valves_to_close=[torch_iso])
auto.release()
print("terminated")
print("ctrl-c to terminate autosequence")
time.sleep(60)
    
