# half inc until 10%, then full inc--replaces cycles

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

mode = input("enter 'real' to connect to GSE or 'sim' to connect to sim: ")

if mode == "real":
    PROOF_PRESS = 1000                              #psi
    TENP_TARGET = PROOF_PRESS * 0.1
    # RATE = 0.02  
    INC_PRESS_REG = 20                                   # seconds - rate of data collection
    INC_PRESS_INIT = INC_PRESS_REG / 2                                  # psi - pressure increment
    INC_DELAY = 20                                   # seconds - delay between increments
    CYCLES_INIT = 3
    billion = 1000000000
    PROOF_DURATION = synnax.TimeSpan(10 * 60 * billion)  # ns - 10 minutes
    PROOF_BOUND = 50

else:
    PROOF_PRESS = 1000                              #psi
    # RATE = 0.02  
    INC_PRESS_REG = 20                                   # seconds - rate of data collection
    INC_PRESS_INIT = INC_PRESS_REG / 2                                  # psi - pressure increment
    INC_DELAY = 20                                   # seconds - delay between increments
    CYCLES_INIT = 3
    billion = 1000000000
    PROOF_DURATION = synnax.TimeSpan(10 * 60 * billion)  # ns - 10 minutes
    PROOF_BOUND = 50


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

def pressurize_tank(
        auto: synnax.control.Controller, 
        target_pressure: float = None,):
        return get_tank_pressure(auto) > target_pressure

def check_lower_bound(
        auto: synnax.control.Controller,
        lower_bound: float,
        max_time: synnax.TimeSpan,
        start_time: synnax.TimeStamp
):
  return get_tank_pressure(auto) < lower_bound or synnax.TimeStamp.now().since(start_time) > max_time

try:
    print(f"PROOF_PRESS: {PROOF_PRESS}")
    print(f"PROOF_DURATION: {PROOF_DURATION}")
    # print(f"CYCLES_INIT: {CYCLES_INIT}")
    print(f"INC_PRESS_INIT: {INC_PRESS_INIT}")
    print(f"INC_PRESS_REG: {INC_PRESS_REG}")
    input("press enter to continue ")
    print("setting system state\n")

    # start by closing everything
    press_valve.close()
    press_vent.close()

    #run initial press cycles
    print("press enter to pressurize")
    print(f"pressurizing by {INC_PRESS_INIT} psi until {TENP_TARGET}")
    partial_target = get_tank_pressure(auto)
    while partial_target < TENP_TARGET:
         partial_target += INC_PRESS_REG
         if partial_target > TENP_TARGET:
              partial_target = TENP_TARGET
              press_valve.open()
              auto.wait_until(lambda c: pressurize_tank(auto, partial_target))
              press_valve.close()
         else: 
              press_valve.open()
              auto.wait_until(lambda c: pressurize_tank(auto, partial_target))
              press_valve.close()
              time.sleep(INC_DELAY)

    print(f"pressurized to {get_tank_pressure(auto)} psi")
    input(f"press enter to pressurize to {PROOF_PRESS} psi (increments of {INC_PRESS_REG})")
    print(f"pressurizing to {PROOF_PRESS}")
    while partial_target < PROOF_PRESS:
         partial_target += INC_PRESS_REG
         if partial_target > PROOF_PRESS:
              partial_target = PROOF_PRESS
              press_valve.open()
              auto.wait_until(lambda c: pressurize_tank(auto, partial_target))
              press_valve.close()
         else: 
              press_valve.open()
              auto.wait_until(lambda c: pressurize_tank(auto, partial_target))
              press_valve.close()
              time.sleep(INC_DELAY)
    
    print(f"proof pressure reached. tank pressure: {get_tank_pressure(auto)}")
    print("beginning proof")
    proof_start = synnax.TimeStamp.now()
    over_yet = synnax.TimeStamp.now().since(proof_start) >= PROOF_DURATION

    try:       
      while synnax.TimeStamp.now().since(proof_start) < PROOF_DURATION:
        print(f"repressurizing for {round((PROOF_DURATION - synnax.TimeStamp.now().since(proof_start)).seconds, 2)}s")
        press_valve.open()
        auto.wait_until(lambda c: pressurize_tank(auto = auto, target_pressure = (PROOF_PRESS) + PROOF_BOUND))
        press_valve.close()
        auto.wait_until(lambda c: check_lower_bound(auto=auto, lower_bound = (PROOF_PRESS) - PROOF_BOUND, max_time = (PROOF_DURATION - (synnax.TimeStamp.now().since(proof_start))), start_time=synnax.TimeStamp.now()))
      print(f"proof complete - tank has been at pressure for {PROOF_DURATION}")

    except KeyboardInterrupt as e:
        print("proof terminated")
        press_valve.close()
    
    input("press enter to release")
    press_vent.open()
    

except KeyboardInterrupt as e:
    print("\naborting")
    press_valve.close()
    press_vent.close()
    print("system has been safed")
