import time
import sys
import synnax as sy
from synnax.control.controller import Controller

import synnax.control.controller
print(synnax.control.controller.__file__)

# this defines a class that can be used for both regular valves and vents
class Valve:
    def __init__(
            self,
            auto: Controller,
            cmd: str,
            name: str = "",
            ack: str = "",
            normally_open: bool = False,
            mawp: float = 0,
            wait_for_ack: bool = False
    ):
        self.name = name
        self.cmd_chan = cmd
        self.ack = ack
        self.normally_open = normally_open
        self.auto = auto
        self.wait_for_ack = wait_for_ack
        self.mawp = mawp

    def open(self):
        # for reg. valve, normally_open is false so cmd is set to True
        # for vent valve, normally_open is true so cmd is set to False
        self.auto[self.cmd_chan] = not self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan != self.normally_open)

    def close(self):
        # for reg. valve, normally_open is false so cmd is set to False
        # for vent valve, normally_open is true so cmd is set to True
        self.auto[self.cmd_chan] = self.normally_open
        if self.wait_for_ack:
            self.auto.wait_until(self.ack_chan == self.normally_open)

    # returns true iff the valve is below the MAWP
    def check_safe(self, pressure: str):
        return self.auto[pressure] < self.mawp


class DualTescomValve:
    def __init__(
        self,
        auto: Controller,
        close_cmd_chan: str,
        open_cmd_chan: str,
        name: str = "",
        normally_open: bool = False,
        mawp: float = 0,
        wait_for_ack: bool = False,
        open_cmd_ack: str = "",
        close_cmd_ack: str = "",
    ):
        self.name = name
        self.normally_open = normally_open
        self.auto = auto
        self.wait_for_ack = wait_for_ack
        self.mawp = mawp
        self.open_cmd_chan = open_cmd_chan
        self.close_cmd_chan = close_cmd_chan
        self.open_cmd_ack = open_cmd_ack
        self.close_cmd_ack = close_cmd_ack

    # energizes the open_cmd_chan valve to open the valve
    def open(self):
        self.auto.set({
            self.close_cmd_chan: False,
            self.open_cmd_chan: True,
        })
        if self.wait_for_ack:
            self.auto.wait_until(self.open_cmd_ack)

    # energizes the close_cmd_chan valve to close the valve

    def close(self):
        self.auto.set({
            self.close_cmd_chan: True,
            self.open_cmd_chan: False,
        })
        if self.wait_for_ack:
            self.auto.wait_until(self.close_cmd_ack)


# def open_close_many_valves(auto: Controller, valves_to_close: list[Valve], valves_to_open: list[Valve]):
#     auto.set({
#         valve.cmd_chan: (not valve.normally_open) if valve in valves_to_close
#         else valve.normally_open
#         for valve in valves_to_open
#     })
            
def open_close_many_valves(auto: Controller, valves_to_open: list[Valve], valves_to_close: list[Valve]):
    commands = {}
    # Close valves to close
    for valve in valves_to_open:
        commands[valve.cmd_chan] = int(True)
    # Open valves to open
    for valve in valves_to_close:
        if valve.normally_open:
            commands[valve.cmd_chan] = int(True)
        else:
            commands[valve.cmd_chan] = int(False)
    
    auto.set(commands)

def close_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: valve.normally_open for valve in valves})


def open_all(auto: Controller, valves: list[Valve]):
    auto.set({valve.cmd_chan: not valve.normally_open for valve in valves})


# this energizes the valve until the target pressure is reached
def pressurize(valve, pressure: str, target: float, inc: float, delay: float = 1):
    partial_target = inc
    while True:
        if isinstance(valve, dict):
            valve_name = valve['name']
            valve_open = valve['open']
            valve_close = valve['close']
            valve_auto = valve['auto']
        elif isinstance(valve, Valve):
            valve_name = valve.name
            valve_open = valve.open
            valve_close = valve.close
            valve_auto = valve.auto
        else:
            raise ValueError("valve parameter must be either a dictionary or a Valve object")
        
        print(f"pressurizing {valve_name} to {partial_target}")
        valve_open()
        valve_auto.wait_until(lambda auto: auto[pressure] >= partial_target)
        valve_close()
        time.sleep(delay)
        if partial_target >= target:
            print(f"{valve_name} has reached {target}")
            break
        partial_target += inc

def purge(valves: list[Valve], duration: float = 1):
    prev_time = time.time()
    for valve in valves:
        while (time.time() - prev_time < duration):
            open_all(valve.auto, valves)
            time.sleep(1)