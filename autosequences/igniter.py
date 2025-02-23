from autosequences import syauto
import time
import synnax as sy
import statistics
from collections import deque
import datetime

### TODO: don't forget to run `synnax login` with the params for the new remote cluster

client = sy.Synnax()

### TODO: confirm these with COP

NITROUS_MPV_VLV = "gse_vlv_1"
NITROUS_MPV_STATE = "gse_state_1"
METHANE_MPV_VLV = "gse_vlv_3"
METHANE_MPV_STATE = "gse_state_3"
NITROUS_PILOT_VLV = "gse_vlv_2"
NITROUS_PILOT_STATE = "gse_state_2"
SPARK_VLV = "gse_vlv_4"
SPARK_STATE = "gse_state_4"

TORCH_PT_1 = "gse_ai_5"
TORCH_PT_2 = "gse_ai_6"
TORCH_PT_3 = "gse_ai_7"

PRESS_SUPPLY = "gse_pt_3"

METHANE_TANK_PT = "gse_pt_5"

NITROUS_TANK_PT = "gse_pt_1"

TORCH_PT_1 = "gse_pt_6"
TORCH_PT_2 = "gse_pt_7"
TORCH_PT_3 = "gse_pt_8"

### TODO: confirm these with TC

IGNITION_TIMEOUT_SECONDS = 2
IGNITION_TIMEOUT = IGNITION_TIMEOUT_SECONDS * (10**9)

# SPARK_SLEEP = 0.04

BURN_DURATION = 2

METHANE_MPV_LEAD_TIME = 0

NITROUS_PILOT_LEAD_TIME = 0.25

TORCH_PT_TARGET = 250

### everything after this should be fine

CMDS = [
    NITROUS_MPV_VLV,
    METHANE_MPV_VLV,
    NITROUS_PILOT_VLV,
    SPARK_VLV,
]
STATES = [
    NITROUS_MPV_STATE,
    METHANE_MPV_STATE,
    NITROUS_PILOT_STATE,
    SPARK_STATE,
]
PTS = [
    METHANE_TANK_PT,
    NITROUS_TANK_PT,
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
    
    def torch_ignite(nitrous_pilot_mpv: syauto.Valve, spark_plug: syauto.Valve, methane_mpv: syauto.Valve, nitrous_mpv: syauto.Valve, NITROUS_PILOT_LEAD_TIME=NITROUS_PILOT_LEAD_TIME, METHANE_MPV_LEAD_TIME=METHANE_MPV_LEAD_TIME 
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
        time.sleep(0.75)
        print("Opening methane and nitrous pilot MPVs")
        methane_mpv.open()
        time.sleep(METHANE_MPV_LEAD_TIME)
        nitrous_pilot_mpv.open()
        # syauto.open_all(auto, [nitrous_pilot_mpv, methane_mpv])
        time.sleep(NITROUS_PILOT_LEAD_TIME)

        print("Commencing ignition sequence")
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

    def abort(spark_plug: syauto.Valve, methane_mpv: syauto.Valve, nitrous_mpv: syauto.Valve, nitrous_pilot_mpv: 
              syauto.Valve):
        print("\n\nManual abort, safing system")
        print("Closing all valves")
        spark_plug.close()
        syauto.close_all(
            auto=auto, valves=[nitrous_mpv, methane_mpv, nitrous_pilot_mpv]
        )
        print("Terminated")
        exit(0)

    def monitor(auto, target = TORCH_PT_TARGET):
        value = statistics.median(
            [auto[TORCH_PT_1], auto[TORCH_PT_2], auto[TORCH_PT_3]]
        )
        if (value >= target):
            return True

    ### TODO: check normally_open values with COP

    nitrous_mpv = syauto.Valve(
        auto=auto, cmd=NITROUS_MPV_VLV, ack=NITROUS_MPV_STATE, normally_open=False
    )

    nitrous_pilot_mpv = syauto.Valve(
        auto=auto, cmd=NITROUS_PILOT_VLV, ack=NITROUS_PILOT_STATE, normally_open=False
    )

    methane_mpv = syauto.Valve(
        auto=auto, cmd=METHANE_MPV_VLV, ack=METHANE_MPV_STATE, normally_open=False
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

        if auto[METHANE_MPV_STATE] == 1:
            ans = input("Methane MPV is open, type 'yes' to confirm close ")
            if ans == "yes" or ans == "Yes":
                print("Closing methane MPV")
                methane_mpv.close()
            else:
                print(
                    "Methane MPV was not prompted to close, moving on with the sequence"
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

        fire = input(
            "Type 'fire' to commence ignition sequence with a 5 second countdown "
        )

        if fire == "fire" or fire == "Fire":

            retry = True
            while retry == True:
                ignited = torch_ignite(nitrous_pilot_mpv, spark_plug, methane_mpv, nitrous_mpv, NITROUS_PILOT_LEAD_TIME, TORCH_PT_TARGET, TORCH_PT_1, TORCH_PT_2, TORCH_PT_3)
                if ignited == True:
                    retry = False
                    print("Torch ignited")
                    time.sleep(BURN_DURATION)
                    print("Closing MPVs and de-energizing spark plug")
                    syauto.close_all(
                        auto=auto, valves=[nitrous_mpv, methane_mpv, nitrous_pilot_mpv]
                    )
                    spark_plug.close()
                    print("Terminating Autosequence")

                    print("Terminated")
                    time.sleep(1)

                else:
                    print("Torch failed to ignite.")
                    syauto.close_all(auto, [nitrous_mpv, methane_mpv, nitrous_pilot_mpv])
                    spark_plug.close()
                    print(f"Methane Tank PT: {auto[METHANE_TANK_PT]} psig")
                    print(f"Nitrous Bottle PT: {auto[NITROUS_TANK_PT]} psig")
                    testAgain = input("Type 'retry' to retry autosequence. ")
                    if testAgain != "retry" and testAgain != "Retry":
                        retry = False

    except KeyboardInterrupt as e:
        abort(spark_plug, methane_mpv, nitrous_mpv, nitrous_pilot_mpv)

time.sleep(2)
