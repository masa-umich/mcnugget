from synnax.control import Controller
import synnax as sy
from typing import Callable

MFV = "fuel_main_valve"
MOV = "ox_main_valve"
FUEL_PREVALVE = "fuel_prevalve"
OX_PREVALVE = "ox_prevalve"
OX_BLEED_VALVE_1 = "ox_bleed_valve"
OX_FEEDLINE_VENT = "ox_feed_line_vent"
IGNITER = "igniter"
TPC_SIG = "tpc_signal"
PREPRESS_SIG = "prepress_signal"
PREPRESS_SIG_ACK = "prepress_signal_ack"
PUMP_BYPASS = "pump_bypass"
PUMP_BYPASS_ACK = "pump_bypass_ack"

IGNITER_DELAY = 100 * sy.TimeSpan.MILLISECOND
MOV_DELAY = 100 * sy.TimeSpan.MILLISECOND
MFV_DELAY = 100 * sy.TimeSpan.MILLISECOND
COUNTDOWN_TIME = 10 * sy.TimeSpan.SECOND
BURN_DURATION = 420 * sy.TimeSpan.SECOND
TPC_EARLY_SHUTDOWN = 500 * sy.TimeSpan.MILLISECOND
PRESSURE_LOSS_MARGIN = 10  # psi
EQUALIZATION_NUMBER = 100 # psi

COPV_TEMP = "copv_temp"
COPV_PRESSURE = "copv_pressure"
GAS_SUPPLY_PRESSURE = "2k_pressure"
COPV_LOW_TEMP_LIMIT = "copv_low_temp_limit"

AIR_DRIVE_1 = "air_drive_1"
AIR_DRIVE_2 = "air_drive_2"
GAS_SUPPLY_VALVE = "gas_booster_fill"
def set_gooster(auto: Controller, v: bool):
    auto.set(AIR_DRIVE_1, v)
    auto.set(AIR_DRIVE_2, v)\
def press(
    auto: Controller,
    pressure_ladder: list[float],
    temp_limit: float,
    set_valves: Callable[[bool], None]
):
    ...
    set_valves(False)
    curr_ladder = 0
    for target in pressure_ladder:
        set_valves(True)
        check = lambda c: c[COPV_PRESSURE] > pressure_ladder[curr_ladder]
        auto.wait_until(check)
        if (auto[GAS_SUPPLY_PRESSURE] - auto[COPV_PRESSURE]) < EQUALIZATION_NUMBER:
            break
        set_valves(False)
        while True:
            auto.wait_until(lambda c: c[COPV_PRESSURE] < (target - PRESSURE_LOSS_MARGIN) or c[COPV_TEMP] < temp_limit)
            if auto[COPV_TEMP] < temp_limit:
                curr_ladder += 1
                break
            set_valves(True)
            auto.wait_until(lambda c: c[COPV_PRESSURE] > target)
            set_valves(False)

def hell(a):
    print(a)

hell = lambda a: print(a)
def press_fill(auto: Controller):
    # auto.set(PUMP_BYPASS, True)
    # if not auto.wait_until(lambda c: c[PUMP_BYPASS_ACK], timeout=150 * sy.TimeSpan.MILLISECOND):
    #     ...
    press(auto, [], COPV_LOW_TEMP_LIMIT, auto.set(PUMP_BYPASS, None))
    auto.set(PUMP_BYPASS, True)
    auto.set(GAS_SUPPLY_VALVE, True)
    press(auto, [], COPV_LOW_TEMP_LIMIT, lambda v: set_gooster(auto, v))





    # Equalize with 2K using a temp press sequence.



def engine(auto: Controller):
    # 1. Go-nogos

    # 2. Countdown - 10s
    # Pre-press maintains pressures

    # 3. All would do holds except for overpressure
    # 1. Pre-flight checks
    # 2. Tank pressures in bounds
    # 3. Press pressures
    # 4. Temperatures
    # 5. Pre-valves open
    # different levels of severity, flags, holds, and total aborts

    auto.set(PREPRESS_SIG, False)
    if not auto.wait_until(lambda c: c[PREPRESS_SIG_ACK], timeout=300 * sy.TimeSpan.MILLISECOND):
        # go back into hold
        ...

    # 3. Igniter opens at COUNTDOWN_TIME - IGNITER_DELAY
    auto.set_delayed({
        [IGNITER]: 5000 * sy.TimeSpan.MILLISECOND,
        [MFV]: 100 * sy.TimeSpan.MILLISECOND,
        [MOV]: 150 * sy.TimeSpan.MILLISECOND,
        [TPC_SIG]: True,
    })

    # Checking for engine condition specific abort cases
    # 1. Fuel temperature
    # 2. Overpressure in Ox anf Fuel tanks
    # Check every cycle
    # Waiting for BURN_DURATION while checking for abort cases
    auto.wait_until(lambda c: False, timeout=BURN_DURATION - TPC_EARLY_SHUTDOWN)
    auto.set({[TPC_SIG]: False})
    auto.wait_until(lambda c: False, timeout=TPC_EARLY_SHUTDOWN)
    auto.set({
        [MFV]: False,
        [MOV]: False,
        [OX_PREVALVE]: False,
        [FUEL_PREVALVE]: False,
    })


def hello_world(contents: str):
    print(contents)


hello_world("Helo dog!")
