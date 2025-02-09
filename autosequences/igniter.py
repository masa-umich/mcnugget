from autosequences import syauto
import time
import synnax as sy
import statistics
from collections import deque
import datetime

client = sy.Synnax()

NITROUS_MPV_VLV = "gse_do_4_0_cmd"
NITROUS_MPV_STATE = "gse_do_4_0_state"
ETHANOL_MPV_VLV = "gse_do_4_1_cmd"
ETHANOL_MPV_STATE = "gse_do_4_1_state"
ETHANOL_VENT_VLV = "gse_do_4_2_cmd"
ETHANOL_VENT_STATE = "gse_do_4_2_state"
TORCH_PURGE_VLV = "gse_do_4_3_cmd"
TORCH_PURGE_STATE = "gse_do_4_3_state"
TORCH_2K_ISO_VLV = "gse_do_4_4_cmd"
TORCH_2K_ISO_STATE = "gse_do_4_4_state"

SPARK_VLV_1 = "gse_do_4_6_cmd"
SPARK_STATE_1 = "gse_do_4_6_state"
SPARK_VLV_2 = "gse_do_4_5_cmd"
SPARK_STATE_2 = "gse_do_4_6_state"

TORCH_PT_1 = "gse_ai_5"
TORCH_PT_2 = "gse_ai_6"
TORCH_PT_3 = "gse_ai_7"

IGNITION_TIMEOUT = 5 * (10**9)  # convert to ns
IGNITION_THRESHOLD = 500
SAMPLES_TO_AVERAGE = 10
AVERAGE_THRESHOLD = 0.8

BURN_DURATION = 3
PURGE_DURATION = 5

MPV_DELAY = 0.075

CMDS = [
    NITROUS_MPV_VLV,
    ETHANOL_MPV_VLV,
    TORCH_2K_ISO_VLV,
    TORCH_PURGE_VLV,
    ETHANOL_VENT_VLV,
    SPARK_VLV_1,
    SPARK_VLV_2,
]
STATES = [
    NITROUS_MPV_STATE,
    ETHANOL_MPV_STATE,
    TORCH_2K_ISO_STATE,
    TORCH_PURGE_STATE,
    ETHANOL_VENT_STATE,
    SPARK_STATE_1,
    SPARK_STATE_2,
]
PTS = [
    TORCH_PT_1,
    TORCH_PT_2,
    TORCH_PT_3,
]

WRITE_TO = []
READ_FROM = []

for cmd in CMDS:
    WRITE_TO.append(cmd)

for ack in STATES:
    READ_FROM.append(ack)

for pt in PTS:
    READ_FROM.append(pt)


with client.control.acquire(
    name="Torch Ignition Booyah", write=WRITE_TO, read=READ_FROM, write_authorities=222
) as auto:

    def monitor(auto, target, start, SUM):
        value = statistics.median(
            [auto[TORCH_PT_1], auto[TORCH_PT_2], auto[TORCH_PT_3]]
        )
        values = deque()
        if value >= target:
            SUM += 1
            values.append(1)
        else:
            values.append(0)
        if len(values) > SAMPLES_TO_AVERAGE:
            SUM -= values.popleft()
        if SUM / len(values) >= AVERAGE_THRESHOLD and len(values) >= SAMPLES_TO_AVERAGE:
            return True
        if sy.TimeStamp.since(start) >= IGNITION_TIMEOUT:
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
        normally_open=False,
    )

    spark_plug_1 = syauto.Valve(
        auto=auto, cmd=SPARK_VLV_1, ack=SPARK_STATE_1, normally_open=False
    )
    spark_plug_2 = syauto.Valve(
        auto=auto, cmd=SPARK_VLV_2, ack=SPARK_STATE_2, normally_open=False
    )

    time.sleep(1)

    try:
        ans = input("Type 'start' to commence autosequence. ")
        if not (ans == "start" or ans == "Start" or ans == "START"):
            exit()

        print("Starting Igniter Autosequence. Setting initial system state.")
        # if auto[TORCH_PURGE_STATE] == 1:
        #     ans = input("Torch Purge is open, type 'yes' to confirm close ")
        #     if ans == "yes" or ans == "Yes":
        #         print("Closing Torch Purge")
        #         torch_purge.close()
        #     else:
        #         print(
        #             "Torch Purge was not prompted to close, moving on with the sequence"
        #         )

        # if auto[ETHANOL_MPV_STATE] == 1:
        #     ans = input("Ethanol MPV is open, type 'yes' to confirm close ")
        #     if ans == "yes" or ans == "Yes":
        #         print("Closing ethanol MPV")
        #         ethanol_mpv.close()
        #     else:
        #         print(
        #             "Ethanol MPV was not prompted to close, moving on with the sequence"
        #         )

        # if auto[NITROUS_MPV_STATE] == 1:
        #     ans = input("Nitrous MPV is open, type 'yes' to confirm close ")
        #     if ans == "yes" or ans == "Yes":
        #         print("Closing nitrous MPV")
        #         nitrous_mpv.close()
        #     else:
        #         print(
        #             "Nitrous MPV was not prompted to close, moving on with the sequence"
        #         )

        # if auto[TORCH_2K_ISO_STATE] == 0:
        #     ans = input("Torch 2K Iso is closed, type 'yes' to confirm opening ")
        #     if ans == "yes" or ans == "Yes":
        #         print("Opening Torch 2K Iso")
        #         torch_iso.open()
        #     else:
        #         print(
        #             "Torch 2K Iso was not prompted to open, moving on with the sequence"
        #         )

        fire = input(
            "Type 'fire' to commence ignition sequence with a 5 second countdown "
        )

        if fire == "fire" or fire == "Fire":

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
                syauto.open_all(auto, [spark_plug_1, spark_plug_2])
                # spark_plug_1.open()
                time.sleep(1)

                print("Commencing ignition sequence")

                print(f"Opening nitrous mpv at {datetime.datetime.now()}")
                nitrous_mpv.open()

                time.sleep(MPV_DELAY)

                print(f"Opening ethanol mpv at {datetime.datetime.now()}")
                ethanol_mpv.open()

                start = sy.TimeStamp.now()

                auto.wait_until(
                    lambda func: monitor(auto, IGNITION_THRESHOLD, start, 0)
                )

                if (
                    statistics.median(
                        [auto[TORCH_PT_1], auto[TORCH_PT_2], auto[TORCH_PT_3]]
                    )
                    >= IGNITION_THRESHOLD
                ):
                    retry = False
                    print("Torch ignited at ", datetime.datetime.now())
                    time.sleep(BURN_DURATION)
                    print("Closing MPVs and Torch 2K Iso at ", datetime.datetime.now())
                    syauto.close_all(
                        auto=auto, valves=[nitrous_mpv, ethanol_mpv, torch_iso]
                    )
                    syauto.close_all(auto, [spark_plug_1, spark_plug_2])
                    # spark_plug_1.close()
                    # print("Purging at ", datetime.datetime.now())
                    # torch_purge.open()
                    # time.sleep(PURGE_DURATION)
                    # torch_purge.close()
                    print("Terminated")
                    time.sleep(1)

                else:
                    print("Torch failed to ignite before ", datetime.datetime.now())
                    syauto.close_all(auto, [nitrous_mpv, ethanol_mpv])
                    syauto.close_all(auto, [spark_plug_1, spark_plug_2])
                    # spark_plug_1.close()
                    # torch_purge.open()
                    # time.sleep(PURGE_DURATION)
                    # torch_purge.close()
                    testAgain = input(
                        "Type 'retry' to retry autosequence or anything else to terminate. "
                    )
                    if testAgain != "retry" and testAgain != "Retry":
                        retry = False

    except KeyboardInterrupt as e:
        print("\n\nManual abort, safing system")
        print("Closing all valves and vents")
        syauto.close_all(auto, [spark_plug_1, spark_plug_2])
        # spark_plug_1.close()
        syauto.open_close_many_valves(
            auto=auto,
            valves_to_close=[ethanol_mpv, nitrous_mpv, torch_iso],
            valves_to_open=[ethanol_tank_vent],
        )
        # torch_purge.open()
        # time.sleep(PURGE_DURATION)
        # torch_purge.close()
        print("Terminated")
        exit(0)

time.sleep(5)
