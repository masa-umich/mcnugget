from synnax.control.controller import Controller
from autosequences import syauto
import time
import synnax as sy
import statistics

NITROUS_MPV_DOC = "gse_doc_1"
NITROUS_MPV_DOA = "gse_doa_1"

ETHANOL_MPV_DOC = "gse_doc_2"
ETHANOL_MPV_DOA = "gse_doa_2"

TORCH_ISO_DOC = "gse_doc_3"
TORCH_ISO_DOA = "gse_doa_3"

TORCH_PURGE_DOC = "gse_doc_4"
TORCH_PURGE_DOA = "gse_doa_4"

ETHANOL_TANK_VENT_DOC = "gse_doc_5"
ETHANOL_TANK_VENT_DOA = "gse_doa_5"

SPARK_PLUG_DOC = "gse_doc_6"
SPARK_PLUG_DOA = "gse_doa_6"

ETHANOL_PRESS_TARGET = 750

CHAMBER_PRESS_TARGET = 100

TORCH_PT_TARGET = 620

PRESS_RATE = 50

torch_ignited = False

retry = True

DURATION_BEFORE_SPARK = 0.19

SECONDS_OF_SPARKING = 3

SPARK_RATE = 25

ETHANOL_TANK_PT = "gse_ai_1"

NITROUS_TANK_PT = "gse_ai_2"

TORCH_PT_1 = "gse_ai_3"
TORCH_PT_2 = "gse_ai_4"
TORCH_PT_3 = "gse_ai_5"

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


def ethanol_press():
    return auto[ETHANOL_TANK_PT] >= ETHANOL_PRESS_TARGET

auto = client.control.acquire(name="Torch Ignition Booyah", write="WRITE_TO", read="READ_FROM", write_authorities=222)

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

    print("Starting Press Fill Autosequence. Setting initial system state.")
    syauto.close_all(auto, [nitrous_mpv, ethanol_mpv, torch_iso, torch_purge, ethanol_tank_vent])
    time.sleep(1)

    print(f"pressurizing ethanol to {ETHANOL_PRESS_TARGET}")
    syauto.open(torch_iso)
    auto.wait_until(ethanol_press)
    syauto.close(torch_iso)

    while(retry == True):
        print("opening ethanol mpv")
        syauto.open(ethanol_mpv)

        time.sleep(.1)

        print("opening nitrous mpv")
        syauto.open(nitrous_mpv)

        time.sleep(DURATION_BEFORE_SPARK)

        while(torch_ignited == False):
            for i in range (SECONDS_OF_SPARKING):
                for j in range(SPARK_RATE):
                    syauto.open(spark_plug)
                    syauto.close(spark_plug)
                    pts_median = statistics.median(auto[TORCH_PT_1],auto[TORCH_PT_2],auto[TORCH_PT_3])
                    if(pts_median >= TORCH_PT_TARGET):
                        torch_ignited = True
                    else:
                        time.sleep(1)
            break

        
        if(torch_ignited == False):
            syauto.close_all(auto, [nitrous_mpv,ethanol_mpv])
            syauto.open(torch_purge)
            time.sleep(2)
            syauto.close(torch_purge)
            print(f"Ethanol Supply: {auto[ETHANOL_TANK_PT]} psig")
            print(f"Nitrous Supply: {auto[NITROUS_TANK_PT]} psig")
            testAgain = input("Type 'retry' to retry autosequence. ")
            if testAgain != 'retry' or testAgain != 'Retry':
                retry = False

except KeyboardInterrupt as e:
    print("Manual abort, safing system")
    print("Closing all valves and vents")
    syauto.open_close_many_valves(auto=auto, valves_to_open=[ethanol_tank_vent], valves_to_close=[ethanol_mpv, nitrous_mpv, torch_iso])
    
    syauto.open(torch_purge)
    time.sleep(2)
    syauto.close(torch_purge)

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
    
