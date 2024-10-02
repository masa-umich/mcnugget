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
MAWP = 850                                      # will target 1.1x MAWP for proofing
MAX_PRESSURE = 0                                # psi (highest recorded pressure)
DROP_THRESHOLD = 150                            # psi
PROOF_DURATION = synnax.TimeSpan(600000)        # nanoseconds
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

# # running average functions:
# running_average_values = {}
# running_average_sums = {}
# running_average_length = 10  # for 50Hz data, this is equivalent to 0.2 seconds

# def read_average(channel: str):
#     return running_average_sums[channel] / len(running_average_values[channel])
     
# def update_average(channel: str, auto: synnax.control.Controller):
#     # read in the most recent value
#     new_value = auto[channel]
    
#     # if the channel is not present in the dictionary, add it
#     if not running_average_values.get(channel):
#         running_average_values[channel] = deque()
#         running_average_sums[channel] = 0
        
#     running_average_sums[channel] += new_value
#     running_average_values[channel].push(new_value)

#     if len(running_average_values[channel]) > running_average_length:
#         # update the sum, and delete the first value
#         running_average_sums[channel] -= running_average_values[channel].popleft()

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

def repressurize_tank(
        auto: synnax.control.Controller,
        lower_bound: float,
        max_time: synnax.TimeSpan,
        start_time: synnax.TimeStamp = synnax.TimeStamp.now()
):
    # returns true if pressure drops below lower_bound or if time exceeds max_time
    return (auto[TANK_PRESSURE_AVG] < lower_bound) or (synnax.TimeStamp.now() - start_time > max_time)
    
def pressurize_tank_monitor_burst(
        auto: synnax.control.Controller, 
        press_method_: press_method, 
        target_pressure: float = None,
        target_delay: float = None,
        start_time: synnax.TimeStamp = synnax.TimeStamp.now()
):
    # def drop(auto):
        # return auto[PRESS_TANK_AVG] + DROP_THRESHOLD < 
    #     curr_avg_pressure = 0
    #     prev_avg_pressure = 0
    #     prev_avg_pressure = curr_avg_pressure
    #     curr_avg_pressure = auto[TANK_PRESSURE_AVG]
    #     return (((curr_avg_pressure - prev_avg_pressure) + DROP_THRESHOLD) < 0)
    print(' i need a better name ')
    match press_method_:
        case press_method.time:
            if not drop(auto): 
                return start_time + target_delay <= synnax.TimeStamp.now() 
            BURST = True 
            return True 
        case press_method.pressure: 
            if not drop(auto):    
                return auto[TANK_PRESSURE_AVG] > BURST_TARGET
            return True
    

# pressurizes tank in increments of 50 for when there is a specified target pressure
# def target_inc_pressurize(auto):

#     global temp_target_pressure
#     while auto[TANK_PRESSURE] + 50 < target_pressure:
#         press_valve.open()
#         temp_target_pressure += 50
#         auto.wait_until(temp_pressurize)
#         press_valve.close()
#         time.sleep(3) 
#     press_valve.open()
#     auto.wait_until(pressurize)
#     press_valve.close()
#     return True     

# returns true if there's a sudden drop in pressure
def drop(auto):
    # global CURR_PRESSURE
    # global PREV_PRESSURE

    # PREV_PRESSURE = CURR_PRESSURE
    # CURR_PRESSURE = auto[TANK_PRESSURE]
    
    # grab the previous avg and current avg
    # subtract prev from curr to see if there is a drop
    curr_avg_pressure = 0
    prev_avg_pressure = 0
    prev_avg_pressure = curr_avg_pressure
    curr_avg_pressure = auto[TANK_PRESSURE_AVG]
    return (((curr_avg_pressure - prev_avg_pressure) + DROP_THRESHOLD) < 0)

# returns true if either (a) temp target pressure is reached or (b) the tank has burst
# also sets BURST to true if tank has burst
# def check_drop(auto):
#      global BURST

#      if auto[TANK_PRESSURE] > temp_target_pressure:
#           return True
#      if drop(auto):
#           BURST = True
#           return True

# incremental pressurization for unspecified target pressure
# def inc_pressurize(auto):
#      global temp_target_pressure
#      temp_target_pressure += 50
#      while not drop(auto):
#         press_valve.open()
#         auto.wait_until(check_drop)
#         if BURST:
#              break
#         press_valve.close()
#         temp_target_pressure += 50
#         time.sleep(3)
#      return True

# # maintains pressure at target pressure
# def keep_pressure(auto):
#      for i in range(300):
#         if auto[TANK_PRESSURE] < target_pressure - 10:
#             press_valve.open()
#             auto.wait_until(pressurize)
#             press_valve.close()
#         time.sleep(2)
#      return True

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
    
    print(f"pressurizing to 1.1x MAWP {MAWP * 1.1}")
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
        while synnax.TimeStamp.now() - proof_start > PROOF_DURATION:
            # press_valve.close()
            auto.wait_until(lambda c: repressurize_tank(auto, lower_bound=(MAWP * 1.1) - MAWP_BOUND))
            press_valve.open()
            auto.wait_until(lambda c: pressurize_tank(auto, PRESS_METHOD, (MAWP * 1.1) + MAWP_BOUND))
            press_valve.close()
    else:
        print("beginning proof, console operator must manually repressurize the system")
        breakdown = 30
        for i in range(breakdown):
            print(f"sleeping for {int(PROOF_DURATION / breakdown)}")
            time.sleep(PROOF_DURATION / breakdown)

    print("pressurizing to burst...")
    partial_target = auto[TANK_PRESSURE_AVG]
    partial_target += BURST_INC_PRESS
    while not BURST:
        if partial_target < ((1.1 * MAWP) + 0.80 * (BURST_TARGET - (1.1 * MAWP))):
            press_valve.open()
            auto.wait_until(lambda c: pressurize_tank(auto, PRESS_METHOD, partial_target, BURST_INC_TIME))
            press_valve.close()
            partial_target += BURST_INC_PRESS
        else: 
            press_valve.open()
            auto.wait_until(lambda c: pressurize_tank(auto, PRESS_METHOD, partial_target, BURST_INC_TIME * 0.5))
            press_valve.close()
            partial_target += BURST_INC_PRESS * 0.5
    # press_valve.open()
    # PREV_PRESSURE = CURR_PRESSURE
    # CURR_PRESSURE = auto[TANK_PRESSURE]
    
    # inc_pressurize(auto)
    # press_valve.close()
    print(f"highest pressure recorded was {MAX_PRESSURE}")

except KeyboardInterrupt as e:
    print("aborting")
    press_valve.close()
    # press_vent.open()

    print("system has been safed")
