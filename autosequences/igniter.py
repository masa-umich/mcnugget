from autosequences import syauto
import time
import synnax as sy
import statistics
from collections import deque

client = sy.Synnax()

NITROUS_MPV_VLV = "gse_vlv_1"
NITROUS_MPV_STATE = "gse_state_1"
ETHANOL_MPV_VLV = "gse_vlv_2"
ETHANOL_MPV_STATE = "gse_state_2"
ETHANOL_VENT_VLV = "gse_vlv_3"
ETHANOL_VENT_STATE = "gse_state_3"
TORCH_PURGE_VLV = "gse_vlv_4"
TORCH_PURGE_STATE = "gse_state_4"
TORCH_2K_ISO_VLV = "gse_vlv_5"
TORCH_2K_ISO_STATE = "gse_state_5"
SPARK_VLV = "gse_vlv_6"
SPARK_STATE = "gse_state_6"

TORCH_PT_TARGET = 620

PRESS_RATE = 50

DURATION_BEFORE_SPARK = 0.19

SECONDS_OF_SPARKING = 3

SPARK_RATE = 25

IGNITION_TIMEOUT = 2 * (10**9)

IGNITION_TIMEOUT_SECONDS = 2

INITIAL_SLEEP = 0.01

SPARK_SLEEP = 0.04

PURGE_DURATION = 2

PRESS_SUPPLY = "gse_pt_3"

ETHANOL_TANK_PT = "gse_pt_5"

NITROUS_TANK_PT = "gse_pt_1"

TORCH_PT_1 = "gse_pt_6"
TORCH_PT_2 = "gse_pt_7"
TORCH_PT_3 = "gse_pt_8"


CMDS = [
    NITROUS_MPV_VLV,
    ETHANOL_MPV_VLV,
    TORCH_2K_ISO_VLV,
    TORCH_PURGE_VLV,
    ETHANOL_VENT_VLV,
    SPARK_VLV,
]
ACKS = [
    NITROUS_MPV_STATE,
    ETHANOL_MPV_STATE,
    TORCH_2K_ISO_STATE,
    TORCH_PURGE_STATE,
    ETHANOL_VENT_STATE,
    SPARK_STATE,
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
    
    def torch_ignite(spark_plug: syauto.Valve, ethanol_mpv: syauto.Valve, nitrous_mpv: syauto.Valve, INITIAL_SLEEP = INITIAL_SLEEP, 
                     TORCH_PT_TARGET = TORCH_PT_TARGET, TORCH_PT_1 = TORCH_PT_1, TORCH_PT_2 = TORCH_PT_2, TORCH_PT_3 = TORCH_PT_3) -> bool:
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

        auto.wait_until(lambda func: monitor(auto, TORCH_PT_TARGET), IGNITION_TIMEOUT_SECONDS)

        if (
            statistics.median(
                [auto[TORCH_PT_1], auto[TORCH_PT_2], auto[TORCH_PT_3]]
            )
            >= TORCH_PT_TARGET
        ):
            return True
        return False

    def abort(spark_plug: syauto.Valve, ethanol_mpv: syauto.Valve, nitrous_mpv: syauto.Valve, torch_iso: 
              syauto.Valve, ethanol_tank_vent: syauto.Valve ,torch_purge: syauto.Valve, PURGE_DURATION = PURGE_DURATION):
        print("\n\nManual abort, safing system")
        print("Closing all valves and vents")
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

    def monitor(auto, target = TORCH_PT_TARGET):
        value = statistics.median(
            [auto[TORCH_PT_1], auto[TORCH_PT_2], auto[TORCH_PT_3]]
        )
        if (value >= target):
            return True

    nitrous_mpv = syauto.Valve(
        auto=auto, cmd=NITROUS_MPV_VLV, ack=NITROUS_MPV_STATE, normally_open=False
    )

    ethanol_mpv = syauto.Valve(
        auto=auto, cmd=ETHANOL_MPV_VLV, ack=ETHANOL_MPV_STATE, normally_open=False
    )

    torch_iso = syauto.Valve(
        auto=auto, cmd=TORCH_2K_ISO_VLV, ack=TORCH_2K_ISO_STATE, normally_open=False
    )

    torch_purge = syauto.Valve(
        auto=auto, cmd=TORCH_PURGE_VLV, ack=TORCH_PURGE_STATE, normally_open=False
    )

    ethanol_tank_vent = syauto.Valve(
        auto=auto,
        cmd=ETHANOL_VENT_VLV,
        ack=ETHANOL_VENT_STATE,
        normally_open=True,
    )

    spark_plug = syauto.Valve(
        auto=auto, cmd=SPARK_VLV, ack=SPARK_STATE, normally_open=False
    )

    time.sleep(1)

    try:
        ans = input("Type 'start' to commence autosequence. ")
        if not (ans == "start" or ans == "Start" or ans == "START"):
            exit()

        print("Starting Igniter Autosequence. Setting initial system state.")
        if auto[TORCH_PURGE_STATE] == 1:
            ans = input("Torch Purge is open, type 'yes' to confirm close ")
            if ans == "yes" or ans == "Yes":
                print("Closing Torch Purge")
                torch_purge.close()
            else:
                print(
                    "Torch Purge was not prompted to close, moving on with the sequence"
                )

        if auto[ETHANOL_MPV_STATE] == 1:
            ans = input("Ethanol MPV is open, type 'yes' to confirm close ")
            if ans == "yes" or ans == "Yes":
                print("Closing ethanol MPV")
                ethanol_mpv.close()
            else:
                print(
                    "Ethanol MPV was not prompted to close, moving on with the sequence"
                )

        if auto[NITROUS_MPV_STATE] == 1:
            ans = input("Nitrous MPV is open, type 'yes' to confirm close ")
            if ans == "yes" or ans == "Yes":
                print("Closing nitrous MPV")
                nitrous_mpv.close()
            else:
                print(
                    "Nitrous MPV was not prompted to close, moving on with the sequence"
                )

        ethanol_tank_vent.close()

        fire = input(
            "Type 'fire' to commence ignition sequence with a 5 second countdown "
        )

        if fire == "fire" or fire == "Fire":

            retry = True
            while retry == True:
                ignited = torch_ignite(spark_plug, ethanol_mpv, nitrous_mpv, INITIAL_SLEEP, TORCH_PT_TARGET, TORCH_PT_1, TORCH_PT_2, TORCH_PT_3)
                if ignited == True:
                    retry = False
                    print("Torch ignited")
                    time.sleep(5)
                    print("Closing MPVs and Torch 2K Iso")
                    syauto.close_all(
                        auto=auto, valves=[nitrous_mpv, ethanol_mpv, torch_iso]
                    )
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
        abort(spark_plug, ethanol_mpv, nitrous_mpv, torch_iso, ethanol_tank_vent, torch_purge, PURGE_DURATION)

time.sleep(5)
