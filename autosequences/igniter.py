from autosequences import syauto
import time
import synnax as sy
import statistics
from collections import deque

client = sy.Synnax()

NITROUS_MPV_DOC = "torch_vlv_0"
NITROUS_MPV_DOA = "torch_state_0"

ETHANOL_MPV_DOC = "torch_vlv_1"
ETHANOL_MPV_DOA = "torch_state_1"

TORCH_ISO_DOC = "torch_vlv_2"
TORCH_ISO_DOA = "torch_state_2"

TORCH_PURGE_DOC = "torch_vlv_4"
TORCH_PURGE_DOA = "torch_state_4"

ETHANOL_TANK_VENT_DOC = "torch_vlv_3"
ETHANOL_TANK_VENT_DOA = "torch_state_3"

SPARK_PLUG_DOC = "torch_vlv_5"
SPARK_PLUG_DOA = "torch_state_5"

TORCH_PT_TARGET = 620

PRESS_RATE = 50

DURATION_BEFORE_SPARK = 0.19

SECONDS_OF_SPARKING = 3

SPARK_RATE = 25

IGNITION_TIMEOUT = 2*(10**9)

INITIAL_SLEEP = 0.01

SPARK_SLEEP = 0.04

PURGE_DURATION = 2

PRESS_SUPPLY = "torch_pt_0"

ETHANOL_TANK_PT = "ethanol_pt_5"

NITROUS_TANK_PT = "nitrous_pt_1"

TORCH_PT_1 = "torch_pt_6"
TORCH_PT_2 = "torch_pt_7"
TORCH_PT_3 = "torch_pt_8"


CMDS = [
    NITROUS_MPV_DOC,
    ETHANOL_MPV_DOC,
    TORCH_ISO_DOC,
    TORCH_PURGE_DOC,
    ETHANOL_TANK_VENT_DOC,
    SPARK_PLUG_DOC,
]
ACKS = [
    NITROUS_MPV_DOA,
    ETHANOL_MPV_DOA,
    TORCH_ISO_DOA,
    TORCH_PURGE_DOA,
    ETHANOL_TANK_VENT_DOA,
    SPARK_PLUG_DOA,
]
PTS = [
    ETHANOL_TANK_PT,
    NITROUS_TANK_PT,
    TORCH_PT_1,
    TORCH_PT_2,
    TORCH_PT_3,
    PRESS_SUPPLY,
]

WRITE_TO = []
READ_FROM = []

for cmd in CMDS:
    WRITE_TO.append(cmd)

for ack in ACKS:
    READ_FROM.append(ack)

for pt in PTS:
    READ_FROM.append(pt)


with client.control.acquire(
    name="Torch Ignition Booyah", write=WRITE_TO, read=READ_FROM, write_authorities=222
) as auto:
    def monitor(auto, target, start, SUM):
        value = statistics.median([auto[TORCH_PT_1], auto[TORCH_PT_2], auto[TORCH_PT_3]])
        values = deque()
        if value >= target:
            SUM += 1
            values.append(1)
        else:
            values.append(0)
        if len(values) > 10:
            SUM -= values.popleft()
        if SUM/len(values) >= 0.8 and len(values) == 10:
            return True
        if(sy.TimeStamp.since(start) >= IGNITION_TIMEOUT): 
            return True

    nitrous_mpv = syauto.Valve(
        auto=auto, cmd=NITROUS_MPV_DOC, ack=NITROUS_MPV_DOA, normally_open=False
    )

    ethanol_mpv = syauto.Valve(
        auto=auto, cmd=ETHANOL_MPV_DOC, ack=ETHANOL_MPV_DOA, normally_open=False
    )

    torch_iso = syauto.Valve(
        auto=auto, cmd=TORCH_ISO_DOC, ack=TORCH_ISO_DOA, normally_open=False
    )

    torch_purge = syauto.Valve(
        auto=auto, cmd=TORCH_PURGE_DOC, ack=TORCH_PURGE_DOA, normally_open=False
    )

    ethanol_tank_vent = syauto.Valve(
        auto=auto,
        cmd=ETHANOL_TANK_VENT_DOC,
        ack=ETHANOL_TANK_VENT_DOA,
        normally_open=True,
    )

    spark_plug = syauto.Valve(
        auto=auto, cmd=SPARK_PLUG_DOC, ack=SPARK_PLUG_DOA, normally_open=False
    )

    try:
        ans = input("Type 'start' to commence autosequence. ")
        if not (ans == "start" or ans == "Start" or ans == "START"):
            exit()

        print("Starting Igniter Autosequence. Setting initial system state.")
        if (auto[TORCH_PURGE_DOA] == 1):
            ans = input("Torch Purge is open, type 'yes' to confirm close ")
            if (ans == 'yes' or ans == 'Yes'):
                print("Closing Torch Purge")
                torch_purge.close()
            else:
                print("Torch Purge was not prompted to close, moving on with the sequence")
        
        if (auto[ETHANOL_MPV_DOA] == 1):
            ans = input("Ethanol MPV is open, type 'yes' to confirm close ")
            if (ans == 'yes' or ans == 'Yes'):
                print("Closing ethanol MPV")
                ethanol_mpv.close()
            else:
                print("Ethanol MPV was not prompted to close, moving on with the sequence")

        if (auto[NITROUS_MPV_DOA] == 1):
            ans = input("Nitrous MPV is open, type 'yes' to confirm close ")
            if (ans == 'yes' or ans == 'Yes'):
                print("Closing nitrous MPV")
                nitrous_mpv.close()
            else:
                print("Nitrous MPV was not prompted to close, moving on with the sequence")

        ethanol_tank_vent.close()


        if (auto[TORCH_ISO_DOA] == 0):
            ans = input("Torch 2K Iso is closed, type 'yes' to confirm opening ")
            if (ans == 'yes' or ans == 'Yes'):
                print("Opening Torch 2K Iso")
                torch_iso.open()
            else:
                print("Torch 2K Iso was not prompted to open, moving on with the sequence")
           

        fire = input("Type 'fire' to commence ignition sequence with a 5 second countdown ")

        if fire == 'fire' or fire == 'Fire':


            retry = True
            while retry == True:

                print("5")
                time.sleep(1)
                print("4")
                time.sleep(1)
                print("3")
                time.sleep(1)
                print("2")
                time.sleep(1)
                print("1")
                print("Energizing Spark Plug")
                spark_plug.open()
                time.sleep(1)
                
                print("Commencing ignition sequence")

                print("Opening ethanol mpv")
                ethanol_mpv.open()

                time.sleep(INITIAL_SLEEP)
                
                print("Opening nitrous mpv")
                nitrous_mpv.open()



                #time.sleep(DURATION_BEFORE_SPARK)

                start = sy.TimeStamp.now()

                auto.wait_until(lambda func: monitor(auto, TORCH_PT_TARGET, start,0))

                if statistics.median([auto[TORCH_PT_1], auto[TORCH_PT_2], auto[TORCH_PT_3]]) >= TORCH_PT_TARGET:
                    retry = False
                    print("Torch ignited")
                    time.sleep(5)
                    print("Closing MPVs and Torch 2K Iso")
                    syauto.close_all(auto=auto, valves=[nitrous_mpv, ethanol_mpv, torch_iso])
                    spark_plug.close()
                    print("Terminating Autosequence")
                    print("Purging")
                    torch_purge.open()
                    time.sleep(PURGE_DURATION)
                    torch_purge.close()
                    print("Terminated")
                    time.sleep(1)


                else:
                    print("Torch failed to ignite.")
                    syauto.close_all(auto, [nitrous_mpv, ethanol_mpv])
                    spark_plug.close()
                    torch_purge.open()
                    time.sleep(PURGE_DURATION)
                    torch_purge.close()
                    print(f"Ethanol Tank PT: {auto[ETHANOL_TANK_PT]} psig")
                    print(f"Nitrous Bottle PT: {auto[NITROUS_TANK_PT]} psig")
                    testAgain = input("Type 'retry' to retry autosequence. ")
                    if testAgain != "retry" and testAgain != "Retry":
                        retry = False
                     

    except KeyboardInterrupt as e:
        print("\n\nManual abort, safing system")
        print("Closing all valves and vents")
        #ethanol_tank_vent.open()
        spark_plug.close()
        syauto.open_close_many_valves(
            auto=auto,
            valves_to_close=[ethanol_mpv, nitrous_mpv, torch_iso],
            valves_to_open=[ethanol_tank_vent],
        )
        torch_purge.open()
        time.sleep(PURGE_DURATION)
        torch_purge.close()
        print("Terminated")
        exit(0)

time.sleep(5)