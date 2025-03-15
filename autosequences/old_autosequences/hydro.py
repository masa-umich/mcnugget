import time
import synnax
import synnax.control
import syauto
import statistics

client = synnax.Synnax()

PRESS_VENT_ACK = "gse_state_5"
PRESS_VENT_CMD = "gse_vlv_5"
VALVE_1_ACK = "gse_state_7"
VALVE_1_CMD = "gse_vlv_7"
# VALVE_2_ACK = "gse_state_6"
# VALVE_2_CMD = "gse_vlv_6"

TANK_PRESSURE_1 = "gse_ai_1_avg"
TANK_PRESSURE_2 = "gse_ai_1_avg"
TANK_PRESSURE_3 = "gse_ai_1_avg"

WRITE_TO = [PRESS_VENT_CMD, VALVE_1_CMD]
READ_FROM = [PRESS_VENT_ACK, VALVE_1_ACK, TANK_PRESSURE_1, TANK_PRESSURE_2, TANK_PRESSURE_3]

client = synnax.Synnax()

PRESS_TARGET = 4500
PRESS_INC = 50
PRESS_DELAY = 5
BOUND = 5
PROOF_DURATION = 10 * 10**9

with client.control.acquire(name="Hydro Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100) as auto:
    print("initializing...")
    time.sleep(1)
    input("press enter to start ")

    press_valve_1 = syauto.Valve(
        auto=auto,
        cmd=VALVE_1_CMD,
        ack=VALVE_1_ACK,
        normally_open=False,
    )

    # press_valve_2 = syauto.Valve(
    #     auto=auto,
    #     cmd=VALVE_2_CMD,
    #     ack=VALVE_2_ACK,
    #     normally_open=False,
    # )

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
        press_valve_1.close()
        # press_valve_2.close()
        press_vent.close()

        ### PRESSURIZE TANK ###
        print(f"pressurizing to MAWP {PRESS_TARGET}")
        partial_target = get_tank_pressure(auto) + PRESS_INC
        partial_target = min(partial_target, PRESS_TARGET)
        pressure = get_tank_pressure(auto)
        while pressure < PRESS_TARGET and partial_target < PRESS_TARGET:
            press_valve_1.open()
            # press_valve_2.open()
            auto.wait_until(lambda c: get_tank_pressure(auto) >= partial_target)
            press_valve_1.close()
            # press_valve_2.close()
            print(f"pressurized to {round(partial_target, 2)}")
            time.sleep(PRESS_DELAY)
            partial_target += PRESS_INC
            partial_target = min(partial_target, PRESS_TARGET)
        input(f"pressure has reached {PRESS_TARGET}, press any key to continue ")

        ### PROOF ###
        proof_start = synnax.TimeStamp.now()
        while synnax.TimeStamp.now().since(proof_start) < PROOF_DURATION:
            auto.wait_until(lambda c: get_tank_pressure(auto) >= (PRESS_TARGET) + BOUND)
            print(f"pressure at {PRESS_TARGET - BOUND}, repressurizing...")
            press_valve_1.open()
            # press_valve_2.open()
            auto.wait_until(lambda c: get_tank_pressure(auto) <= (PRESS_TARGET) - BOUND)
            press_valve_1.close()
            # press_valve_2.close()
            print(f"pressure at {PRESS_TARGET + BOUND}, repressurization complete.")
        input("proof complete, press enter to terminate ")

    except KeyboardInterrupt as e:
        print("aborting...")
        press_valve_1.close()
        vent = input("vent? y/n")
        if vent == "y":
            press_vent.open()
        # press_valve_2.close()

time.sleep(1)