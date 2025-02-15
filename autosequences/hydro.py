import time
import synnax
import synnax.control
import syauto
import statistics

client = synnax.Synnax()

PRESS_VALVE_ACK = "gse_doa_1"
PRESS_VALVE_CMD = "gse_doc_1"
PRESS_VENT_ACK = "gse_doa_7"
PRESS_VENT_CMD = "gse_doc_7"

TANK_PRESSURE_1 = "gse_ai_9_avg"
TANK_PRESSURE_2 = "gse_ai_10_avg"
TANK_PRESSURE_3 = "gse_ai_11_avg"

WRITE_TO = [PRESS_VENT_CMD, PRESS_VALVE_CMD]
READ_FROM = [PRESS_VENT_ACK, PRESS_VALVE_ACK, TANK_PRESSURE_1, TANK_PRESSURE_2, TANK_PRESSURE_3]

client = synnax.Synnax()

PRESS_TARGET = 100
PRESS_INC = 10
PRESS_DELAY = 1
BOUND = 5
PROOF_DURATION = 10 * 10**9

with client.control.acquire(name="Hydro Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100) as auto:
    print("initializing...")
    time.sleep(1)

    press_valve = syauto.Valve(
        auto=auto,
        cmd=PRESS_VALVE_CMD,
        ack=PRESS_VALVE_ACK,
        normally_open=False,
    )

    press_vent = syauto.Valve(
        auto=auto,
        cmd=PRESS_VENT_CMD,
        ack=PRESS_VENT_ACK,
        normally_open=False,
    )

    def get_tank_pressure(auto: synnax.control.Controller):
        return statistics.median([auto[TANK_PRESSURE_1],
                                auto[TANK_PRESSURE_2],
                                auto[TANK_PRESSURE_3]])

    try:
        ### STARTING STATE ###
        press_valve.close()
        press_vent.close()

        ### PRESSURIZE TANK ###
        print(f"pressurizing to MAWP {PRESS_TARGET}")
        partial_target = get_tank_pressure(auto) + PRESS_INC
        pressure = get_tank_pressure(auto)
        while pressure < PRESS_TARGET and partial_target < PRESS_TARGET:
            press_valve.open()
            auto.wait_until(lambda c: get_tank_pressure(auto) >= partial_target)
            press_valve.close()
            print(f"pressurized to {round(partial_target, 2)}")
            time.sleep(PRESS_DELAY)
            partial_target += PRESS_INC
        input(f"pressure has reached {PRESS_TARGET}, press any key to continue ")

        ### PROOF ###
        proof_start = synnax.TimeStamp.now()
        while synnax.TimeStamp.now().since(proof_start) < PROOF_DURATION:
            auto.wait_until(lambda c: get_tank_pressure(auto) >= (PRESS_TARGET) + BOUND)
            print(f"pressure at {PRESS_TARGET - BOUND}, repressurizing...")
            press_valve.open()
            auto.wait_until(lambda c: get_tank_pressure(auto) <= (PRESS_TARGET) - BOUND)
            press_valve.close()
            print(f"pressure at {PRESS_TARGET + BOUND}, repressurization complete.")
        input("proof complete, press enter to terminate ")

    except KeyboardInterrupt as e:
        print("aborting...")
        press_valve.close()

time.sleep(1)