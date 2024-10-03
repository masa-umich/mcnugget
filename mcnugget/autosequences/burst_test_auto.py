import time
import synnax
import synnax.control
from collections import deque
from enum import Enum
from mcnugget.autosequences import syauto

# this initializes a connection to the Synnax server
client = synnax.Synnax()

# these are the channel names we will be using
PRESS_VALVE_ACK = "gse_doa_1"
PRESS_VALVE_CMD = "gse_doc_1"
PRESS_VENT_ACK = "gse_doa_2"
PRESS_VENT_CMD = "gse_doc_2"
TANK_PRESSURE = "gse_ai_1"
SUPPLY_PRESSURE = "gse_ai_2"
TANK_PRESSURE_AVG = "gse_ai_1"
SUPPLY_PRESSURE_AVG = "gse_ai_2"

WRITE_TO = [PRESS_VENT_CMD, PRESS_VALVE_CMD]
READ_FROM = [PRESS_VENT_ACK, PRESS_VALVE_ACK, TANK_PRESSURE, SUPPLY_PRESSURE]

"""
We want variables to store
press increment (time version, pressure version)
method of incrementing (time or pressure)
press delay
"""

class press_method(Enum):
    time = 0,
    pressure = 1

INC_PRESS = 50                                  # psi
INC_TIME = 0.5                                  # seconds
INC_DELAY = 1                                   # seconds
PRESS_METHOD = press_method.pressure            # either pressure or time
# MAWP = 850                                      # will target 1.1x MAWP for proofing
MAWP = 300                                      # will target 1.1x MAWP for proofing
MAX_PRESSURE = 0                                # psi (highest recorded pressure)
DROP_THRESHOLD = 150                            # psi
billion = 1000000000
PROOF_DURATION = synnax.TimeSpan(10 * billion)   # nanoseconds again
MAWP_BOUND = 50                                 # psi

BURST_TARGET = 1300
BURST_INC_PRESS = INC_PRESS
BURST_INC_TIME = INC_TIME
BURST_INC_DELAY = INC_DELAY
BURST = False                                   # whether the tank has burst

# this acquires control of the autosequence, creating a controller which we can use to interact with the system
auto = client.control.acquire(name="Demo Autosequence", read=READ_FROM, write=WRITE_TO, write_authorities=100)

print("initializing...")
time.sleep(1)

# this creates a valve object which we can use to open and close the valve
# syauto is a utility library we made to abstract away some of the more confusing parts of the controller
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
    normally_open=True,
)

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
            return auto[TANK_PRESSURE_AVG] > target_pressure

def check_lower_bound(
        auto: synnax.control.Controller,
        lower_bound: float,
        max_time: synnax.TimeSpan,
        start_time: synnax.TimeStamp
):
    # returns true if pressure drops below lower_bound or if time exceeds max_time
    return auto[TANK_PRESSURE_AVG] < lower_bound or synnax.TimeStamp.now().since(start_time) > max_time
    # return synnax.TimeStamp.now().since(start_time) > max_time
    
def pressurize_tank_monitor_burst(
        auto: synnax.control.Controller, 
        press_method_: press_method, 
        target_pressure: float = None,
        target_delay: float = None,
        start_time: synnax.TimeStamp = synnax.TimeStamp.now()
):
    # def drop(auto):
        # return auto[TANK_PRESSURE_AVG] + DROP_THRESHOLD < MAX_PRESSURE
        # curr_avg_pressure = 0
        # prev_avg_pressure = 0
        # prev_avg_pressure = curr_avg_pressure
        # curr_avg_pressure = auto[TANK_PRESSURE_AVG]
        # return (((curr_avg_pressure - prev_avg_pressure) + DROP_THRESHOLD) < 0)
    # print(' i need a better name ')
    match press_method_:
        case press_method.time:
            # if not drop(auto): 
            return start_time + target_delay <= synnax.TimeStamp.now() 
            # BURST = True 
            # return True 
        case press_method.pressure: 
            # if not drop(auto):    
            return auto[TANK_PRESSURE_AVG] > target_pressure
            # return True

try:
    # good idea to add some safety checks
    input("confirm you would like to start autosequence (press enter)")
    print("setting system state\n")

    # start by closing everything
    press_valve.close()
    press_vent.close()

    print(f"pressurizing to MAWP {MAWP}")
    partial_target = auto[TANK_PRESSURE_AVG]  # starting pressure
    partial_target += INC_PRESS
    while partial_target < MAWP:
        press_valve.open()
        auto.wait_until(lambda c: pressurize_tank(auto, PRESS_METHOD, partial_target, INC_TIME))
        press_valve.close()
        time.sleep(INC_DELAY)
        partial_target += INC_PRESS
        partial_target = min(partial_target, MAWP)

    input("pressure has reached MAWP, press any key to continue ")
    
    print(f"pressurizing to 1.1x MAWP {round(MAWP * 1.1, 2)}")
    while partial_target < (MAWP * 1.1):
        press_valve.open()
        auto.wait_until(lambda c: pressurize_tank(auto, PRESS_METHOD, partial_target, INC_TIME))
        press_valve.close()
        time.sleep(INC_DELAY)
        partial_target += INC_PRESS
        partial_target = min(partial_target, MAWP * 1.1)

    print("pressure has reached MAWP * 1.1")

    if PRESS_METHOD == press_method.pressure:
        print("beginning TPC")
        proof_start = synnax.TimeStamp.now()
        over_yet = synnax.TimeStamp.now().since(proof_start) >= PROOF_DURATION
        
        while synnax.TimeStamp.now().since(proof_start) < PROOF_DURATION:
            # press_valve.close()
            print(f"repressurizing for {PROOF_DURATION - synnax.TimeStamp.now().since(proof_start)}")
            auto.wait_until(lambda c: check_lower_bound(auto=auto, lower_bound=(MAWP * 1.1) - MAWP_BOUND, max_time=(PROOF_DURATION - (synnax.TimeStamp.now().since(proof_start))), start_time=synnax.TimeStamp.now()))
            press_valve.open()
            auto.wait_until(lambda c: pressurize_tank(auto=auto, press_method_=PRESS_METHOD, target_pressure=(MAWP * 1.1) + MAWP_BOUND))
            press_valve.close()
    else:
        print("beginning proof, console operator must manually repressurize the system")
        breakdown = 30
        for i in range(breakdown):
            print(f"sleeping for {int(PROOF_DURATION / breakdown)}")
            time.sleep(PROOF_DURATION / breakdown)

    print(f"proof complete - tank has been at pressure for {PROOF_DURATION}")
    input("press any key to continue")
    print("pressurizing to burst...")
    partial_target = auto[TANK_PRESSURE_AVG]
    partial_target += BURST_INC_PRESS
    while not BURST:
        # if less than 80% of way to est. burst
        if partial_target < ((1.1 * MAWP) + 0.80 * (BURST_TARGET - (1.1 * MAWP))):
            press_valve.open()
            auto.wait_until(lambda c: pressurize_tank_monitor_burst(auto, PRESS_METHOD, partial_target, BURST_INC_TIME))
            press_valve.close()
            partial_target += BURST_INC_PRESS
        else: 
            press_valve.open()
            auto.wait_until(lambda c: pressurize_tank_monitor_burst(auto, PRESS_METHOD, partial_target, BURST_INC_TIME * 0.5))
            press_valve.close()
            partial_target += BURST_INC_PRESS * 0.5
    # press_valve.open()
    # PREV_PRESSURE = CURR_PRESSURE
    # CURR_PRESSURE = auto[TANK_PRESSURE]
    
    # inc_pressurize(auto)
    # press_valve.close()
    print(f"highest pressure recorded was {MAX_PRESSURE}")

except KeyboardInterrupt as e:
    print("\naborting")
    press_valve.close()
    press_vent.close()
    # press_vent.open()

    print("system has been safed")
