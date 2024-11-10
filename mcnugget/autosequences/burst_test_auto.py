import time
import synnax
import synnax.control
from collections import deque
from enum import Enum
from mcnugget.autosequences import syauto
import statistics

client = synnax.Synnax()

PRESS_VALVE_ACK = "gse_doa_1"
PRESS_VALVE_CMD = "gse_doc_1"
PRESS_VENT_ACK = "gse_doa_7"
PRESS_VENT_CMD = "gse_doc_7"
# TANK_PRESSURE = "gse_ai_1_avg"

TANK_PRESSURE_1 = "gse_ai_9_avg"
TANK_PRESSURE_2 = "gse_ai_10_avg"
TANK_PRESSURE_3 = "gse_ai_11_avg"

TANK_PRESSURE_OLD_1 = "gse_ai_9_avg_delay"
TANK_PRESSURE_OLD_2 = "gse_ai_10_avg_delay"
TANK_PRESSURE_OLD_3 = "gse_ai_11_avg_delay"
# SUPPLY_PRESSURE = "gse_ai_2_avg"

WRITE_TO = [PRESS_VENT_CMD, PRESS_VALVE_CMD]
READ_FROM = [PRESS_VENT_ACK, PRESS_VALVE_ACK, TANK_PRESSURE_1, TANK_PRESSURE_2, TANK_PRESSURE_3, TANK_PRESSURE_OLD_1, TANK_PRESSURE_OLD_2, TANK_PRESSURE_OLD_3]

class press_method(Enum):
    time = 0,
    pressure = 1

mode = input("enter 'real' to connect to GSE or 'sim' to connect to sim: ")

if mode == "real":
    RATE = 0.02                                     # seconds - rate of data collection
    PRESS_METHOD = press_method.pressure            # press_method - used to determine how to increment pressure
    INC_PRESS = 50                                  # psi - pressure increment
    INC_TIME = 2                                    # seconds - time increment
    INC_DELAY = 20                                   # seconds - delay between increments
    MAWP = 850                                      # psi - maximum allowable working pressure
    billion = 1000000000
    PROOF_DURATION = synnax.TimeSpan(10 * 60 * billion)  # ns - 10 minutes
    MAWP_BOUND = 20                                 # psi
    DROP_THRESHOLD = 100                            # psi - threshold to qualify 'burst'

    BURST_TARGET = 1250                             # psi - estimated burst
    BURST_INC_PRESS = INC_PRESS                     # psi - pressure increment used for burst phase
    BURST_INC_TIME = INC_TIME                       # seconds - time increment used for burst phase
    BURST_INC_DELAY = INC_DELAY                     # seconds - delay used for burst phase
    BURST = False                                   # bool - whether the tank has burst

else:
    DROP_THRESHOLD = 100                            # psi - threshold to qualify 'burst'
    RATE = 0.02                                     # seconds - rate of data collection
    INC_PRESS = 50                                  # psi - pressure increment
    INC_TIME = 2                                    # seconds - time increment
    INC_DELAY = 1                                   # seconds - delay between increments
    PRESS_METHOD = press_method.pressure            # press_method - used to determine how to increment pressure
    MAWP = 850                                      # psi - maximum allowable working pressure
    billion = 1000000000
    PROOF_DURATION = synnax.TimeSpan(30 * billion)   # ns - 5 seconds
    MAWP_BOUND = 50                                 # psi

    BURST_TARGET = 1300                             # psi - estimated burst
    BURST_INC_PRESS = INC_PRESS                     # psi - pressure increment used for burst phase
    BURST_INC_TIME = INC_TIME                       # seconds - time increment used for burst phase
    BURST_INC_DELAY = INC_DELAY                     # seconds - delay used for burst phase
    BURST = False                                   # bool - whether the tank has burst


auto = client.control.acquire(name="Burst Test Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100)

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

def get_old_tank_pressure(auto: synnax.control.Controller):
    return statistics.median([auto[TANK_PRESSURE_OLD_1],
                             auto[TANK_PRESSURE_OLD_2],
                             auto[TANK_PRESSURE_OLD_3]])

def pressurize_tank(
        auto: synnax.control.Controller, 
        press_method_: press_method, 
        target_pressure: float = None,
        target_delay: float = None,
        start_time: synnax.TimeStamp = synnax.TimeStamp.now()):
    match press_method_:
        case press_method.time:
            return start_time + target_delay <= synnax.TimeStamp.now()
        case press_method.pressure:
            return get_tank_pressure(auto) > target_pressure

def check_lower_bound(
        auto: synnax.control.Controller,
        lower_bound: float,
        max_time: synnax.TimeSpan,
        start_time: synnax.TimeStamp
):
    return get_tank_pressure(auto) < lower_bound or synnax.TimeStamp.now().since(start_time) > max_time
    
def pressurize_tank_monitor_burst(
        auto: synnax.control.Controller, 
        press_method_: press_method, 
        target_pressure: float = None,
        target_delay: float = None,
        start_time: synnax.TimeStamp = synnax.TimeStamp.now()
):
    match press_method_:
        case press_method.time:
            return start_time + target_delay <= synnax.TimeStamp.now() or get_tank_pressure(auto) + DROP_THRESHOLD <= get_old_tank_pressure(auto) 
        case press_method.pressure: 
            return get_tank_pressure(auto) > target_pressure or get_tank_pressure(auto) + DROP_THRESHOLD <= get_old_tank_pressure(auto)

try:
    print(f"MAWP: {MAWP} +/- {MAWP_BOUND}")
    print(f"PRESS_METHOD: {PRESS_METHOD}")
    print(f"PROOF_DURATION: {PROOF_DURATION}")
    print(f"BURST_TARGET: {BURST_TARGET}")
    print(f"DROP_THRESHOLD: {DROP_THRESHOLD}")
    print("before MAWP:")
    if PRESS_METHOD == press_method.pressure:
        print(f"\tINC_PRESS: {INC_PRESS}")
    else:
        print(f"\tINC_TIME: {INC_TIME}")
    print(f"\tINC_DELAY: {INC_DELAY}")
    print("after MAWP:")
    if PRESS_METHOD == press_method.pressure:
        print(f"\tINC_PRESS: {BURST_INC_PRESS}")
    else:
        print(f"\tINC_TIME: {BURST_INC_TIME}")
    print(f"\tINC_DELAY: {BURST_INC_DELAY}")
    print()
    input("press enter to continue ")
    print("setting system state\n")

    # start by closing everything
    press_valve.close()
    press_vent.close()

    print(f"pressurizing to MAWP {MAWP}")
    partial_target = get_tank_pressure(auto)  # starting pressure
    partial_target += INC_PRESS
    pressure = get_tank_pressure(auto)
    while pressure < MAWP and partial_target < MAWP:
        press_valve.open()
        auto.wait_until(lambda c: pressurize_tank(auto, PRESS_METHOD, partial_target, INC_TIME))
        press_valve.close()
        print(f"pressurized to {round(partial_target, 2)}")
        time.sleep(INC_DELAY)
        match PRESS_METHOD:
            case press_method.pressure:
                partial_target += INC_PRESS
                partial_target = min(partial_target, MAWP)
            case press_method.time:
                partial_target = get_tank_pressure(auto)
        pressure = get_tank_pressure(auto)

    input("pressure has reached MAWP, press any key to continue ")
    
    print(f"pressurizing to 1.1x MAWP {round(MAWP * 1.1, 2)}")
    while partial_target < (MAWP * 1.1):
        press_valve.open()
        auto.wait_until(lambda c: pressurize_tank(auto, PRESS_METHOD, partial_target, INC_TIME))
        press_valve.close()
        time.sleep(INC_DELAY)
        if PRESS_METHOD == press_method.pressure:
            partial_target += INC_PRESS
            partial_target = min(partial_target, MAWP * 1.1)
        else:
            partial_target = get_tank_pressure(auto)

    print("pressure has reached MAWP * 1.1")

    try:
        if PRESS_METHOD == press_method.pressure:
            print("beginning TPC")
            proof_start = synnax.TimeStamp.now()
            over_yet = synnax.TimeStamp.now().since(proof_start) >= PROOF_DURATION
            
            while synnax.TimeStamp.now().since(proof_start) < PROOF_DURATION:
                # press_valve.close()
                print(f"repressurizing for {round((PROOF_DURATION - synnax.TimeStamp.now().since(proof_start)).seconds, 2)}s")
                press_valve.open()
                auto.wait_until(lambda c: pressurize_tank(auto=auto, press_method_=PRESS_METHOD, target_pressure=(MAWP * 1.1) + MAWP_BOUND))
                press_valve.close()
                auto.wait_until(lambda c: check_lower_bound(auto=auto, lower_bound=(MAWP * 1.1) - MAWP_BOUND, max_time=(PROOF_DURATION - (synnax.TimeStamp.now().since(proof_start))), start_time=synnax.TimeStamp.now()))
        else:
            print("beginning proof, console operator must manually repressurize the system")
            breakdown = 30
            print(f"PROOF_DURATION: {PROOF_DURATION.seconds}s")
            for i in range(breakdown):
                print(f"sleeping for {int(PROOF_DURATION.seconds / breakdown)} seconds")
                time.sleep(PROOF_DURATION.seconds / breakdown)
        print(f"proof complete - tank has been at pressure for {PROOF_DURATION}")

    except KeyboardInterrupt as e:
        print("proof terminated")
        press_valve.close()

    partial_target = get_tank_pressure(auto)
    partial_target += BURST_INC_PRESS
    while True:
        bursting = input("press enter to continue to burst or ctrl+c to terminate the autosequence ")
        print("pressurizing to burst...")
        partial_target = get_tank_pressure(auto)
        BURST = False
        while not BURST:
            # if less than 80% of way to est. burst
            if partial_target < ((1.1 * MAWP) + 0.80 * (BURST_TARGET - (1.1 * MAWP))):
                print(f"presurizing to {round(partial_target, 2)}")
                press_valve.open()
                auto.wait_until(lambda c: pressurize_tank_monitor_burst(auto, PRESS_METHOD, partial_target, BURST_INC_TIME))
                press_valve.close()
                if get_tank_pressure(auto) + DROP_THRESHOLD <= get_old_tank_pressure(auto):
                    break
                partial_target += BURST_INC_PRESS
                time.sleep(BURST_INC_DELAY)
            else: 
                print(f"presurizing for {round(BURST_INC_TIME * 0.5, 2)}")
                press_valve.open()
                auto.wait_until(lambda c: pressurize_tank_monitor_burst(auto, PRESS_METHOD, partial_target, BURST_INC_TIME * 0.5))
                press_valve.close()
                if get_tank_pressure(auto) + DROP_THRESHOLD <= get_old_tank_pressure(auto):
                    break
                partial_target += BURST_INC_PRESS * 0.5
                time.sleep(BURST_INC_DELAY)
        print("tank has burst!")

except KeyboardInterrupt as e:
    print("\naborting")
    press_valve.close()
    press_vent.close()
    print("system has been safed")
